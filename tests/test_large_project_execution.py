"""Large-project classification, source export and real namespace boundary controls."""

from __future__ import annotations

import json
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.large_projects.adapters import CP_CONTROLS, GO_CONTROLS, GO_REGRESSIONS, Command
from benchmarks.large_projects.export import export_parent
from benchmarks.large_projects.grading import classify, go_checks, python_checks
from benchmarks.large_projects.isolation import LinuxBoundary
from benchmarks.large_projects.runner import environment, outcome, prepare_set, verify_preparation
from benchmarks.process import Execution
from tests.test_large_project_handoff import CuratorPreparationTests


class ClassificationTests(unittest.TestCase):
    """Setup problems and missing/skip results must never become valid controls."""

    def test_closed_commands_use_short_private_tmpdir(self) -> None:
        """Deep configurable workspace paths cannot make server Unix sockets too long."""
        root = Path("/arbitrary") / ("deep-output-" * 20)
        self.assertEqual(environment(root, [], network=False)["TMPDIR"], "/tmp")
        self.assertEqual(environment(root, [], network=True)["TMPDIR"], str(root / "tmp"))

    def test_strict_negative_and_positive_controls(self) -> None:
        """Only an observed expected test failure qualifies a negative control."""
        result = Execution(["test"], 1, "", "", 1)
        expected = {"regression": "fail", "control": "pass"}
        self.assertEqual(classify(result, expected, expected), "qualified")
        for bad in (
            {},
            {"regression": "fail"},
            {**expected, "extra": "pass"},
            {**expected, "control": "skip"},
            {**expected, "regression": "error"},
        ):
            self.assertEqual(classify(result, bad, expected), "environment_failure")
        result.timed_out = True
        self.assertEqual(classify(result, expected, expected), "environment_failure")
        result.timed_out = False
        result.returncode = 0
        self.assertEqual(classify(result, expected, expected), "environment_failure")
        self.assertEqual(
            classify(result, dict.fromkeys(expected, "pass"), expected), "behavior_mismatch"
        )

    def test_go_discovery_and_skip(self) -> None:
        """Package success and unrelated tests cannot substitute for required tests."""
        events = [
            json.dumps({"Action": "run", "Test": "Required"}),
            json.dumps({"Action": "pass", "Package": "queue"}),
            json.dumps({"Action": "pass", "Test": "Other"}),
            json.dumps({"Action": "skip", "Test": "Required"}),
        ]
        self.assertEqual(go_checks("\n".join(events), ["Required"]), {"Required": "skip"})
        self.assertEqual(go_checks("\n".join(events[:3]), ["Required"]), {})
        self.assertEqual(go_checks("\n".join(events + events), ["Required"]), {})
        self.assertEqual(python_checks("OK (0 tests)", ["Required"]), {})

    def test_case_roles_do_not_mislabel_passing_controls(self) -> None:
        """The two non-discriminating Collector checks stay pass-to-pass."""
        self.assertEqual(
            GO_REGRESSIONS,
            ["TestCondSignalDoesNotBlockBehindCanceledWaiters", "TestCondCancellationNotification"],
        )
        self.assertNotIn(
            "TestBlockedOfferCancellationDoesNotConsumeCapacityNotification", GO_CONTROLS
        )
        self.assertIn("TestCondSignalAccounting", GO_CONTROLS)
        self.assertEqual(len(CP_CONTROLS), 6)
        self.assertNotIn("test_parallel_module_init", CP_CONTROLS)

    def test_go_descendant_skips_missing_terminals_and_internal_timeouts(self) -> None:
        """A passing parent cannot hide skips or missing children; timeout is setup failure."""
        events = [
            {"Action": "run", "Test": "Required"},
            {"Action": "run", "Test": "Required/child"},
            {"Action": "skip", "Test": "Required/child"},
            {"Action": "pass", "Test": "Required"},
        ]
        text = "\n".join(json.dumps(e) for e in events)
        command = Command("required", [], Path("."), parser="go", expected={"Required": "pass"})
        self.assertEqual(outcome(command, Execution([], 0, text, "", 1))[0], "environment_failure")
        missing = "\n".join(json.dumps(e) for e in [*events[:2], events[-1]])
        self.assertEqual(
            outcome(command, Execution([], 0, missing, "", 1))[0], "environment_failure"
        )
        command.expected = {"Required": "fail"}
        timed = (
            json.dumps({"Action": "run", "Test": "Required"})
            + "\n"
            + json.dumps(
                {"Action": "fail", "Test": "Required", "Output": "panic: test timed out after 60s"}
            )
        )
        self.assertEqual(outcome(command, Execution([], 1, timed, "", 1))[0], "environment_failure")
        self.assertEqual(
            outcome(
                command,
                Execution(
                    [],
                    1,
                    timed.replace("panic: test timed out after 60s", "WARNING: DATA RACE"),
                    "",
                    1,
                ),
            )[0],
            "environment_failure",
        )

    def test_browser_exact_roles_not_totals(self) -> None:
        """Swapping regression/control outcomes or replacing pending identity fails."""
        expected = {"observable": "fail", "control": "pass", "known pending": "skip"}
        command = Command("browser", [], Path("."), parser="mocha", expected=expected)

        def result(passed: str, failed: str, pending: str) -> Execution:
            data = {
                "stats": {"tests": 3},
                "passes": [{"title": passed}],
                "failures": [{"title": failed}],
                "pending": [{"title": pending}],
            }
            return Execution([], 1, json.dumps(data, indent=2), "", 1)

        self.assertEqual(
            outcome(command, result("control", "observable", "known pending"))[0], "qualified"
        )
        self.assertEqual(
            outcome(command, result("observable", "control", "known pending"))[0],
            "behavior_mismatch",
        )
        self.assertEqual(
            outcome(command, result("control", "observable", "different pending"))[0],
            "environment_failure",
        )

    def test_postgres_harness_failure_is_not_negative_control(self) -> None:
        """An unsuccessful test process or absent six-schedule evidence cannot qualify."""
        command = Command(
            "regressions-1",
            [],
            Path("."),
            parser="postgres",
            expected={"tablespace-dependency-locking": "fail"},
        )
        for text, error in [
            (
                "tablespace-dependency-locking ... FAILED (test process exited with exit code 2)\n",
                "",
            ),
            ("1: tablespace-dependency-locking ... FAILED\n", "could not launch isolation tester"),
            ("1: tablespace-dependency-locking ... FAILED\n", ""),
        ]:
            self.assertEqual(
                outcome(command, Execution([], 1, text, error, 1))[0], "environment_failure"
            )

    def test_preparation_timeout_receipts_continue_the_set(self) -> None:
        """Every timed-out download has a retained attempt row and does not hide later cases."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "set"
            ids = ["vscode-snippet-selections", "cpython-import-locks"]
            with patch(
                "benchmarks.large_projects.runner.prepare",
                side_effect=[
                    subprocess.TimeoutExpired(["git", "fetch"], 300),
                    {"case_id": ids[1], "ready_for_model_comparison": False},
                ],
            ):
                results = prepare_set(ids, root)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["status"], "environment_failure")
            self.assertTrue((root / (ids[0] + ".json")).is_file())
            self.assertTrue((root / (ids[1] + ".json")).is_file())

    def test_passing_parent_is_behavior_mismatch(self) -> None:
        """A parent that passes is non-discriminating, rather than an environment failure."""
        for name in GO_REGRESSIONS:
            output = "\n".join(
                json.dumps({"Action": action, "Test": name}) for action in ("run", "pass")
            )
            command = Command("regression", [], Path("."), parser="go", expected={name: "fail"})
            self.assertEqual(
                outcome(command, Execution([], 0, output, "", 1))[0], "behavior_mismatch"
            )

    def test_postgres_tap_plan_and_discovery(self) -> None:
        """Exact TAP identities and complete execution are required for passing controls."""
        expected = {"ddl-dependency-locking": "pass", "drop-owned-grant": "pass"}
        command = Command("controls", [], Path("."), parser="postgres", expected=expected)
        good = (
            "# initializing database system\n"
            "ok 1       - ddl-dependency-locking       245 ms\n"
            "ok 2       - drop-owned-grant              24 ms\n1..2\n"
        )
        self.assertEqual(outcome(command, Execution([], 0, good, "", 1))[0], "qualified")
        for bad in (
            good.replace("1..2", "1..3"),
            good.replace("drop-owned-grant", "other"),
            good.replace("24 ms", "24 ms # SKIP"),
            good.replace("ok 2", "ok 1"),
        ):
            self.assertEqual(
                outcome(command, Execution([], 0, bad, "", 1))[0], "environment_failure"
            )

    def test_clean_handles_readonly_go_cache_and_preserves_receipts(self) -> None:
        """Read-only module directories are removed without following unrelated symlinks."""
        from benchmarks.large_projects.__main__ import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "qualification"
            cache = root / "parent/cache/go-mod/example@v1"
            cache.mkdir(parents=True)
            (cache / "module.go").write_text("fixture")
            outside = Path(directory) / "unrelated"
            outside.mkdir()
            (outside / "keep").write_text("keep")
            (cache / "alias").symlink_to(outside, target_is_directory=True)
            cache.chmod(0o555)
            (root / "qualification.json").write_text("{}")
            (root / "parent/00-command.json").write_text("{}")
            main(["clean", str(root)])
            self.assertFalse((root / "parent/cache").exists())
            self.assertTrue((root / "parent/00-command.json").is_file())
            self.assertEqual((outside / "keep").read_text(), "keep")


class ExportTests(CuratorPreparationTests):
    """Use a local upstream to detect hidden tests, fixes and source contamination."""

    def test_export_has_no_answers_or_history(self) -> None:
        """Archive the untouched parent, not the parent-plus-hidden-tests worktree."""
        from benchmarks.large_projects.prepare import prepare

        curator = self.root / "curator"
        prepare(self.case, curator)
        case = {**self.case, "task": "Fix the observed behavior"}
        # An ignored compiled artifact in a curator worktree must not leak into exports.
        (curator / "parent/ignored-fixed-binary").write_text("answer")
        destination = self.root / "candidate"
        export_parent(case, curator, destination)
        self.assertEqual((destination / "module.txt").read_text(), "broken\n")
        self.assertEqual((destination / "tests.txt").read_text(), "old control\n")
        self.assertFalse((destination / ".git").exists())
        self.assertFalse((destination / "ignored-fixed-binary").exists())
        self.assertEqual((destination / "TASK.md").read_text(), case["task"] + "\n")
        with self.assertRaises(FileExistsError):
            export_parent(case, curator, destination)

    def test_modified_test_content_is_not_a_preparation_receipt(self) -> None:
        """A trusted-looking receipt cannot authenticate edited tests."""
        from benchmarks.large_projects.prepare import prepare

        curator = self.root / "curator"
        prepare(self.case, curator)
        (curator / "parent/tests.txt").write_text("fake test")
        with self.assertRaisesRegex(ValueError, "test contents"):
            verify_preparation(self.case, curator)

    def test_export_rejects_chained_symlink_escape(self) -> None:
        """Lexically safe paths cannot escape by resolving through another source symlink."""
        (self.upstream / "base").symlink_to(".", target_is_directory=True)
        (self.upstream / "escape").symlink_to("base/../outside")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "symlink fixture")
        revision = self.run_git("rev-parse", "HEAD").decode().strip()
        curator = self.root / "curator-links"
        curator.mkdir()
        (curator / "repository").symlink_to(self.upstream, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "chained source symlink"):
            export_parent(
                {**self.case, "parent": revision, "task": "fixture"},
                curator,
                self.root / "unsafe-export",
            )


@unittest.skipUnless(sys.platform == "linux" and shutil.which("bwrap"), "requires Linux Bubblewrap")
class BoundaryTests(unittest.TestCase):
    """Exercise the actual filesystem/network boundary, not a mocked executor."""

    def setUp(self) -> None:
        """Create outside and inside canaries and a minimal private runtime home."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inside = self.root / "workspace"
        self.inside.mkdir()
        self.secret = self.root / "curator-secret"
        self.secret.write_text("answer")
        self.boundary = LinuxBoundary(self.inside)
        self.addCleanup(self.boundary.close)
        # Namespace creation is required in the supported Linux environment.
        self.boundary.preflight([self.secret])

    def test_canaries_and_outside_write(self) -> None:
        """Canaries require a real live listener and positive interpreter/file controls."""
        result = self.boundary.execute(
            [
                "/usr/bin/python3",
                "-c",
                "from pathlib import Path; Path('/usr/toolkit-canary').write_text('changed')",
            ],
            self.inside,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.secret.read_text(), "answer")

    def test_local_harness_network_is_available(self) -> None:
        """A namespace may host its own local server while host listeners stay hidden."""
        script = (
            "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); "
            "c=socket.socket(); c.connect(s.getsockname()); a,_=s.accept(); "
            "c.sendall(b'local'); assert a.recv(5)==b'local'; print('local harness works')"
        )
        result = self.boundary.execute(["/usr/bin/python3", "-c", script], self.inside)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_timeout_and_success_kill_detached_children(self) -> None:
        """A child that creates a new session still dies with the PID namespace."""
        for mode in ("success", "failure", "timeout"):
            timeout = mode == "timeout"
            marker = self.inside / f"leak-{mode}"
            child = f"import time,pathlib; time.sleep(.5); pathlib.Path({str(marker)!r}).touch()"
            script = (
                f"import subprocess,time; subprocess.Popen(['/usr/bin/python3','-c',"
                f"{child!r}],start_new_session=True); "
                + (
                    "time.sleep(10)"
                    if timeout
                    else "raise SystemExit(7)"
                    if mode == "failure"
                    else "print('done')"
                )
            )
            result = self.boundary.execute(
                ["/usr/bin/python3", "-c", script], self.inside, timeout=0.2 if timeout else 5
            )
            self.assertEqual(result.timed_out, timeout)
            if not timeout:
                self.assertEqual(result.returncode, 7 if mode == "failure" else 0, result.stderr)
            time.sleep(0.6)
            self.assertFalse(marker.exists(), "task-owned detached child survived cleanup")

    def test_controller_cancellation_kills_task_descendants(self) -> None:
        """Interrupting the controller unwinds the shared runner and kills detached children."""
        marker = self.inside / "cancel-leak"
        started = self.inside / "cancel-started"
        child = f"import time,pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).touch()"
        command = (
            "import subprocess,time,pathlib; "
            f"subprocess.Popen(['/usr/bin/python3','-c',{child!r}],start_new_session=True); "
            f"pathlib.Path({str(started)!r}).touch(); time.sleep(10)"
        )
        driver = (
            "from pathlib import Path; "
            "from benchmarks.large_projects.isolation import LinuxBoundary; "
            f"b=LinuxBoundary(Path({str(self.inside)!r})); "
            f"b.execute(['/usr/bin/python3','-c',{command!r}],Path({str(self.inside)!r}))"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", driver], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            deadline = time.monotonic() + 5
            while not started.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(started.exists(), "controller failed to launch task")
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=5)
            self.assertNotEqual(process.returncode, 0)
            time.sleep(1.1)
            self.assertFalse(marker.exists(), "task-owned child survived controller cancellation")
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
