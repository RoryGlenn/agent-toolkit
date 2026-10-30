"""Exercise the actual optional site check against local readiness fixtures.

This suite is separate from test_*.py discovery because it requires the optional
Node tools and Playwright Chromium. It does not install dependencies or contact
external services.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar

ROOT = Path(__file__).resolve().parents[1]


class FixtureHandler(BaseHTTPRequestHandler):
    """Serve self-contained HTML and count requests for pre-navigation checks."""

    request_count = 0

    def do_GET(self) -> None:
        """Return a fixture without referencing any remote resources."""
        type(self).request_count += 1
        content = "<main><h1>Guide</h1><p>Loading documentation...</p></main>"
        script = ""
        if self.path in {"/delayed-clean", "/delayed-violation"}:
            button = '<button id="late-button"></button>' if "violation" in self.path else ""
            loaded = f"<h1>Guide</h1><p>Documentation ready</p>{button}"
            script = (
                "<script>setTimeout(() => {"
                "const main = document.querySelector('main');"
                f"main.innerHTML = {json.dumps(loaded)};"
                "main.style.minHeight = '1600px';"
                "main.dataset.docReady = 'true';"
                "}, 2000);</script>"
            )
        elif self.path == "/hidden":
            content += '<div data-doc-ready="true" hidden>Hidden marker</div>'
        elif self.path == "/duplicate":
            content += '<p data-doc-ready="true">One</p><p data-doc-ready="true">Two</p>'
        html = (
            '<!doctype html><html lang="en"><head><title>Guide</title></head>'
            f"<body>{content}{script}</body></html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format: str, *args: Any) -> None:
        """Keep HTTP access logs out of test assertion output."""


class BrowserReadinessTests(unittest.TestCase):
    """Run the shipped Playwright configuration and spec without rewriting them."""

    tooling: ClassVar[Path]
    node: ClassVar[str]
    server: ClassVar[ThreadingHTTPServer]
    server_thread: ClassVar[threading.Thread]

    @classmethod
    def setUpClass(cls) -> None:
        """Start a loopback-only server for the duration of this suite."""
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """Close the fixture server and wait for its worker to stop."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)

    def setUp(self) -> None:
        """Give each assertion case an isolated Playwright output directory."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.outputs = Path(self.temporary.name)

    def run_check(
        self, page: str, selector: str | None
    ) -> tuple[subprocess.CompletedProcess[str], Path, int]:
        """Invoke the production check with controlled URL and readiness inputs.

        Parameters
        ----------
        page : str
            Local fixture route.
        selector : str or None
            Readiness selector; None omits the setting.

        Returns
        -------
        tuple
            Process result, output directory, and observed HTTP request count.
        """
        output = self.outputs / f"run-{len(list(self.outputs.iterdir()))}"
        env = os.environ.copy()
        env["DOC_AGENT_BASE_URL"] = f"http://127.0.0.1:{self.server.server_port}{page}"
        env.pop("DOC_AGENT_READY_SELECTOR", None)
        if selector is not None:
            env["DOC_AGENT_READY_SELECTOR"] = selector
        FixtureHandler.request_count = 0
        result = subprocess.run(
            [
                self.node,
                str(self.tooling / "node_modules/@playwright/test/cli.js"),
                "test",
                "--config",
                str(self.tooling / "playwright.config.mjs"),
                "--output",
                str(output),
            ],
            cwd=self.tooling,
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        return result, output, FixtureHandler.request_count

    def read_artifacts(self, output: Path) -> dict[str, Any]:
        """Check that the saved screenshot contains fully rendered content.

        Parameters
        ----------
        output : Path
            Playwright result directory.

        Returns
        -------
        dict[str, Any]
            Persisted axe results.
        """
        screenshots = list(output.rglob("rendered-page.png"))
        reports = list(output.rglob("accessibility-results.json"))
        self.assertEqual(len(screenshots), 1)
        self.assertEqual(len(reports), 1)
        png = screenshots[0].read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertGreaterEqual(width, 1280)
        self.assertGreaterEqual(height, 1600, "Screenshot captured the loading shell")
        result: dict[str, Any] = json.loads(reports[0].read_text())
        return result

    def test_delayed_accessible_content_is_captured_and_passes(self) -> None:
        """The clean page passes only after its ready marker and tall content appear."""
        result, output, _ = self.run_check("/delayed-clean", '[data-doc-ready="true"]')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.read_artifacts(output)["violations"], [])

    def test_delayed_violation_fails_and_keeps_evidence(self) -> None:
        """An accessibility defect arriving with ready content cannot falsely pass."""
        result, output, _ = self.run_check("/delayed-violation", '[data-doc-ready="true"]')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        violations = self.read_artifacts(output)["violations"]
        buttons = [item for item in violations if item["id"] == "button-name"]
        self.assertTrue(buttons, violations)
        self.assertIn("#late-button", json.dumps(buttons))

    def test_missing_or_blank_selector_fails_before_navigation(self) -> None:
        """Unconfigured readiness cannot accidentally audit a loading page."""
        for selector in (None, "", "   "):
            with self.subTest(selector=selector):
                result, output, requests = self.run_check("/delayed-clean", selector)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DOC_AGENT_READY_SELECTOR", result.stdout + result.stderr)
                self.assertEqual(requests, 0)
                self.assertEqual(list(output.rglob("rendered-page.png")), [])
                self.assertEqual(list(output.rglob("accessibility-results.json")), [])

    def test_missing_or_hidden_marker_times_out_without_audit(self) -> None:
        """Readiness must be visible and satisfy the bounded wait."""
        for page in ("/never", "/hidden"):
            with self.subTest(page=page):
                result, output, _ = self.run_check(page, '[data-doc-ready="true"]')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Timeout", result.stdout + result.stderr)
                self.assertEqual(list(output.rglob("rendered-page.png")), [])
                self.assertEqual(list(output.rglob("accessibility-results.json")), [])

    def test_duplicate_or_invalid_selector_does_not_fall_back(self) -> None:
        """Ambiguous or invalid readiness configuration must fail rather than guess."""
        for selector in ('[data-doc-ready="true"]', "["):
            with self.subTest(selector=selector):
                result, output, _ = self.run_check("/duplicate", selector)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(output.rglob("rendered-page.png")), [])
                self.assertEqual(list(output.rglob("accessibility-results.json")), [])


def main() -> int:
    """Run optional browser regressions only when explicitly requested.

    Returns
    -------
    int
        Zero if tests pass, one for failed tests, two for missing dependencies.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tooling", type=Path, default=ROOT / "skills/documentation-skill/tooling")
    args = parser.parse_args()
    tooling = args.tooling.expanduser().resolve()
    node = shutil.which("node")
    if not node or not (tooling / "node_modules/@playwright/test/cli.js").is_file():
        print("Install the optional Node tools and Chromium as described in the tooling guide.")
        return 2
    BrowserReadinessTests.tooling = tooling
    BrowserReadinessTests.node = node
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BrowserReadinessTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
