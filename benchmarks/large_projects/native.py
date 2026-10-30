"""Model-free qualification of the actual native tool and shared descendant budget.

A local scripted Responses server supplies tool calls and accounting units, never a model
or credentials. The real CLI, Code Mode host, proxy and child sessions execute unchanged.
"""

from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from benchmarks.files import read_regular
from benchmarks.large_projects.resources import ResourceCell, require
from benchmarks.runtime import config_text, digest, fingerprint

DRIVER = Path(__file__).parent / "controls/native-driver.py.txt"


def package_identity(codex: Path) -> dict[str, str]:
    """A standalone executable lacking its matching host/resources cannot qualify."""
    root = codex.parent.parent
    paths = (codex, codex.parent / "codex-code-mode-host", root / "codex-resources/bwrap")
    return {str(path.relative_to(root)): digest(path) for path in paths}


def validate_native(evidence: dict[str, Any], mode: str) -> dict[str, Any]:
    """Require positive actual tool execution and terminal native enforcement evidence."""
    if (
        evidence.get("readonly_unchanged") is not True
        or evidence.get("outside_unchanged") is not True
    ):
        raise ValueError("native tool changed a protected file")
    events = [json.loads(line) for line in evidence["stdout"].splitlines()]
    if mode == "network":
        checks = None
        for event in events:
            item = event.get("item", {})
            if item.get("type") == "command_execution" and item.get("exit_code") == 0:
                for line in item.get("aggregated_output", "").splitlines():
                    try:
                        value = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(value, dict) and "allowed_workspace" in value:
                        checks = value
        if not checks or any(
            checks.get(k) is not True
            for k in (
                "allowed_workspace",
                "allowed_readonly",
                "allowed_local_http",
                "allowed_local_tcp",
                "denied_alias",
                "denied_hardlink",
                "denied_proc_alias",
                "denied_git_object",
            )
        ):
            raise ValueError("actual native tool did not execute all positive/escape controls")
        if any(
            checks.get(key, {}).get("errno") not in (1, 2, 13)
            for key in ("client", "outside", "host_repository")
        ):
            raise ValueError("actual native tool read a forbidden positive target")
        if checks.get("readonly_write", {}).get("errno") not in (1, 13, 30):
            raise ValueError("actual native tool could overwrite readonly input")
        if checks.get("raw_host", {}).get("errno") not in (1, 13, 101):
            raise ValueError("actual native tool reached the live host network")
        if "unexpected" in checks.get("host_loopback", {}):
            raise ValueError("actual native tool reached a host loopback listener")
        if not any(
            "domain is not on the allowlist" in json.dumps(item)
            for item in evidence.get("tools", [])
        ):
            raise ValueError("managed proxy denial was not observed through the actual tool")
        if evidence.get("returncode") != 0 or not any(
            e.get("type") == "turn.completed" for e in events
        ):
            raise ValueError("network probe did not complete")
        return {"status": "passed", "checks": checks, "nonlocal_proxy": "denied_not_allowlisted"}
    failed = any(
        event.get("type") == "turn.failed"
        and event.get("error", {}).get("message") == "shared rollout token budget exhausted"
        for event in events
    )
    if evidence.get("returncode") != 1 or not failed:
        raise ValueError("native shared descendant budget did not stop the root")
    sessions = []
    for session in evidence.get("sessions", []):
        metadata: dict[str, Any] = {}
        tokens = None
        for event in session["events"]:
            payload = event.get("payload", {})
            if event.get("type") == "session_meta" and not metadata:
                metadata = payload
            if payload.get("type") == "token_count" and payload.get("info"):
                tokens = payload["info"]["total_token_usage"]["total_tokens"]
        sessions.append(
            {"id": metadata.get("id"), "source": metadata.get("source"), "tokens": tokens}
        )
    unique: dict[str, dict[str, Any]] = {}
    for session in sessions:
        key = session["id"]
        if not isinstance(key, str):
            raise ValueError("native session identity missing")
        if key in unique and unique[key] != session:
            raise ValueError("conflicting native session metadata")
        unique[key] = session
    sessions = list(unique.values())
    roots = [s for s in sessions if s["tokens"] == 10]
    children = [s for s in sessions if s["tokens"] == 60]
    if len(roots) != 1 or len(children) != 1:
        raise ValueError("missing root or real-child usage evidence")
    source = children[0]["source"]
    if (
        not isinstance(source, dict)
        or source.get("subagent", {}).get("thread_spawn", {}).get("parent_thread_id")
        != roots[0]["id"]
    ):
        raise ValueError("budget control child is not bound to the actual root")
    return {
        "status": "passed",
        "limit_weighted_units": 50,
        "observed_units": 70,
        "overshoot_units": 20,
        "sessions": sessions,
        "scope": "actual root+descendant native accounting; completion-boundary overshoot",
    }


def preflight(
    cell: ResourceCell,
    root: Path,
    codex: Path,
    host_file: Path,
    gitdir: Path,
    oid: str,
    *,
    toolchains: list[Path] | None = None,
    receipts: Path | None = None,
) -> dict[str, Any]:
    """Probe this cell before credentials or a real model invocation are provisioned."""
    # Known-positive host targets cannot be confused with nonexistent-file denial.
    read_regular(host_file)
    from benchmarks.large_projects.prepare import git

    git(gitdir, "cat-file", "-e", oid)
    object_directory = Path(git(gitdir, "rev-parse", "--absolute-git-dir").decode().strip())
    hits: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: Any) -> None:
            pass

        def do_GET(self) -> None:
            hits.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"positive-host-listener")

    listener = ThreadingHTTPServer(("0.0.0.0", 0), Handler)
    thread = threading.Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    address = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        address.connect(("192.0.2.1", 80))  # Route lookup only; no packet is sent.
        host_ip = address.getsockname()[0]
    finally:
        address.close()
    host_port = listener.server_port
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    positive = opener.open(f"http://{host_ip}:{host_port}/host-positive", timeout=2)
    if positive.read() != b"positive-host-listener":
        raise ValueError("host listener positive control failed")
    results = {}
    readonly = [codex.parent.parent, *(toolchains or [])]
    with tempfile.TemporaryDirectory(prefix="toolkit-native-control-") as directory:
        stage = Path(directory)
        (stage / "probe.py").write_bytes(read_regular(DRIVER))
        original = require(cell.execute(["/bin/cat", str(root / "client-home/config.toml")])).stdout
        require(
            cell.execute(
                [
                    str(Path(sys.executable).resolve()),
                    "-c",
                    "import pathlib,sys; r=pathlib.Path(sys.argv[1]); "
                    "(r/'actor-home/readonly-canary').write_text('readonly-positive'); "
                    "(r/'outside-canary').write_text('controller-private')",
                    str(root),
                ]
            )
        )
        try:
            cell.upload(stage / "probe.py", root / "client-home/probe.py")
            for mode in ("network", "budget"):
                config = 'model_provider = "mock"\n' + config_text(
                    root / "workspace",
                    root / "actor-home",
                    root / "client-home",
                    root / "private-tmp",
                    "gpt-6.1-sol",
                    "low",
                    50 if mode == "budget" else 1000,
                    local_network=True,
                    readonly_extra=readonly,
                )
                config += (
                    '\n[model_providers.mock]\nname = "scripted control, no model"\n'
                    'base_url = "http://127.0.0.1:MOCKPORT/v1"\nwire_api = "responses"\n'
                    "requires_openai_auth = false\nrequest_max_retries = 0\n"
                    "stream_max_retries = 0\n"
                )
                template = stage / "config.template"
                template.write_text(config)
                cell.upload(template, root / "client-home/config.template")
                execution = require(
                    cell.execute(
                        [
                            str(Path(sys.executable).resolve()),
                            str(root / "client-home/probe.py"),
                            str(root),
                            mode,
                            str(codex),
                            str(Path(sys.executable).resolve()),
                            host_ip,
                            str(host_port),
                            str(host_file),
                            str(object_directory),
                            oid,
                        ],
                        timeout=75,
                    )
                )
                evidence = json.loads(execution.stdout)
                if receipts is not None:
                    receipts.mkdir(parents=True, exist_ok=True)
                    (receipts / f"native-{mode}.json").write_text(
                        json.dumps(evidence, indent=2) + "\n"
                    )
                results[mode] = {**validate_native(evidence, mode), "evidence": evidence}
            if hits != ["/host-positive"]:
                raise ValueError("candidate tools contacted the live host listener")
        finally:
            restored = stage / "original.toml"
            restored.write_text(original)
            cell.upload(restored, root / "client-home/config.toml")
            require(
                cell.execute(
                    [
                        "/bin/rm",
                        "-f",
                        str(root / "workspace/allowed"),
                        str(root / "workspace/.proof-alias"),
                        str(root / "workspace/.proof-hardlink"),
                    ]
                )
            )
            listener.shutdown()
            listener.server_close()
    return {
        "status": "passed",
        "native_package": package_identity(codex),
        "controls": results,
        "driver_sha256": digest(DRIVER),
        "host_positive_targets": [str(host_file), str(gitdir)],
        "fingerprint": fingerprint({"package": package_identity(codex), "driver": digest(DRIVER)}),
    }
