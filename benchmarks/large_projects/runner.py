"""Model-free, append-only large-project qualification with bounded command receipts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from benchmarks.large_projects.adapters import Command
from benchmarks.large_projects.grading import browser_checks, classify, go_checks, python_checks
from benchmarks.large_projects.prepare import CATALOG, git, prepare, test_patch
from benchmarks.process import sanitized_environment


def write_json(path: Path, value: Any) -> None:
    """Write a new evidence file; never replace an earlier attempt."""
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha(path: Path) -> str:
    """Hash an evidence or source file without loading a large log into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def harness_hashes() -> dict[str, str]:
    """Bind local adapters, common execution/CLI code, catalog and alternative control."""
    package = Path(__file__).parent
    paths = [
        *package.glob("*.py"),
        *package.glob("*.json"),
        *package.glob("controls/*"),
        *package.glob("vendor/*"),
        package.parent / "process.py",
        package.parent / "__main__.py",
        package.parent / "runtime.py",
        package.parent / "files.py",
    ]
    return {str(p.relative_to(package.parent)): sha(p) for p in paths if p.is_file()}


RUNNER_HASHES = harness_hashes()


def environment(root: Path, toolchains: list[Path], *, network: bool) -> dict[str, str]:
    """Use private caches; proxy trust is available only during dependency prefetch."""
    env = sanitized_environment(root / "home", root / "tmp")
    env.update(
        {
            "PATH": ":".join([*(str(p / "bin") for p in toolchains), "/usr/bin", "/bin"]),
            "LANG": "C",
            "LC_ALL": "C",
            "GOMAXPROCS": "2",
            "GOFLAGS": "-mod=readonly",
            "GOTOOLCHAIN": "local",
            "GOWORK": "off",
            "GOCACHE": str(root / "cache/go-build"),
            "GOMODCACHE": str(root / "cache/go-mod"),
            "GOPATH": str(root / "cache/go-path"),
            "npm_config_cache": str(root / "cache/npm"),
            "npm_config_userconfig": "/dev/null",
            "npm_config_jobs": "2",
            "CI": "true",
            "PG_TEST_TIMEOUT_DEFAULT": "30",
            "XDG_CACHE_HOME": str(root / "cache/xdg"),
            "PLAYWRIGHT_BROWSERS_PATH": str(root / "cache/playwright"),
        }
    )
    if network:
        for key in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "http_proxy",
            "https_proxy",
            "NO_PROXY",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "NODE_EXTRA_CA_CERTS",
        ):
            if key in os.environ:
                env[key] = os.environ[key]
    else:
        env.update({"GOPROXY": "off", "GOSUMDB": "off", "npm_config_offline": "true"})
        # This is a private tmpfs in each command namespace. Host output paths can
        # exceed the Unix socket limit when PostgreSQL appends its socket name.
        env["TMPDIR"] = "/tmp"
    return env


def outcome(
    command: Command, result: Any, read_text: Callable[[Path], str] | None = None
) -> tuple[str, dict[str, Any]]:
    """Classify required tests separately from setup and reference-only diagnostics."""
    checks: dict[str, Any] = {}
    combined = result.stdout + result.stderr
    if command.parser.startswith("go") and any(
        marker in combined
        for marker in (
            "panic: test timed out after",
            "WARNING: DATA RACE",
            "[build failed]",
        )
    ):
        return "environment_failure", checks
    if command.parser == "go-all":
        names = []
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            name = event.get("Test", "")
            if event.get("Action") == "run" and name and "/" not in name:
                names.append(name)
        checks = go_checks(result.stdout, names)
        if not checks or result.timed_out or result.output_limited or result.returncode:
            return "environment_failure", checks
        return (
            "passed" if all(v == "pass" for v in checks.values()) else "environment_failure"
        ), checks
    if command.parser == "go":
        known_deadlock = command.expected == {"TestCondCancellationNotification": "fail"}
        checks = go_checks(
            result.stdout, list(command.expected), allow_detected_deadlock=known_deadlock
        )
        if (
            command.expected.get("TestCondSignalDoesNotBlockBehindCanceledWaiters") == "fail"
            and checks.get("TestCondSignalDoesNotBlockBehindCanceledWaiters") == "fail"
        ):
            if "Signal blocked while holding the condition lock" not in combined:
                return "environment_failure", checks
        if (
            known_deadlock
            and checks.get("TestCondCancellationNotification") == "fail"
            and "panic: deadlock: all goroutines in bubble are blocked" not in combined
        ):
            return "environment_failure", checks
    elif command.parser == "python":
        checks = python_checks(result.stdout, list(command.expected))
    elif command.parser == "python-diagnostic":
        checks = python_checks(result.stdout, []) if not result.stdout else {}
        for line in result.stdout.splitlines():
            if line.startswith("TOOLKIT_TESTS="):
                checks = json.loads(line.removeprefix("TOOLKIT_TESTS="))
        return (
            "passed"
            if checks
            and not result.timed_out
            and not result.output_limited
            and result.returncode == 0
            else "environment_failure"
        ), checks
    elif command.parser == "postgres":
        if any(
            marker in combined.lower()
            for marker in (
                "test process",
                "could not",
                "failed to",
                "timeout",
                "fatal:",
                "server closed",
            )
        ):
            return "environment_failure", checks
        # PostgreSQL 20 pg_regress emits TAP. Require its complete plan and exact names.
        rows = re.findall(
            r"^(not )?ok\s+(\d+)\s+[-+]\s+(\S+)\s+[\d.]+ ms\s*$", result.stdout, re.MULTILINE
        )
        plans = re.findall(r"^1\.\.(\d+)\s*$", result.stdout, re.MULTILINE)
        if (
            plans != [str(len(command.expected))]
            or len(rows) != len(command.expected)
            or [int(row[1]) for row in rows] != list(range(1, len(rows) + 1))
            or {row[2] for row in rows} != set(command.expected)
        ):
            return "environment_failure", checks
        checks = {name: "fail" if negative else "pass" for negative, _, name in rows}
        if command.expected.keys() == {"tablespace-dependency-locking"}:
            if not postgres_schedules(command, read_text):
                return "environment_failure", checks
    elif command.parser == "mocha":
        counts, tests = browser_checks(result.stdout)
        if (
            result.timed_out
            or result.output_limited
            or not counts
            or set(tests) != set(command.expected)
        ):
            return "environment_failure", {"counts": counts, "tests": tests}
        expected_exit = 1 if any(value == "fail" for value in tests.values()) else 0
        if result.returncode != expected_exit:
            return "environment_failure", {"counts": counts, "tests": tests}
        return ("qualified" if tests == command.expected else "behavior_mismatch"), {
            "counts": counts,
            "tests": tests,
        }
    else:
        return (
            "passed"
            if result.returncode == 0 and not result.timed_out and not result.output_limited
            else "environment_failure"
        ), checks
    return classify(result, checks, command.expected), checks


def postgres_schedules(command: Command, read_text: Callable[[Path], str] | None = None) -> bool:
    """Require all six real result permutations and the intended semantic mismatches."""
    paths = {}
    for arg in command.argv:
        if arg.startswith(("--outputdir=", "--inputdir=")):
            key, value = arg.split("=", 1)
            paths[key] = Path(value)
    if set(paths) != {"--outputdir", "--inputdir"}:
        return False
    actual_path = paths["--outputdir"] / "results/tablespace-dependency-locking.out"
    expected_path = paths["--inputdir"] / "expected/tablespace-dependency-locking.out"
    try:
        actual, expected = (
            (read_text or Path.read_text)(actual_path),
            (read_text or Path.read_text)(expected_path),
        )
    except (OSError, RuntimeError):
        return False
    actual_parts = actual.split("starting permutation: ")[1:]
    expected_parts = expected.split("starting permutation: ")[1:]
    if len(actual_parts) != 6 or len(expected_parts) != 6:
        return False
    for observed, reference in zip(actual_parts, expected_parts, strict=True):
        if observed.splitlines()[0] != reference.splitlines()[0]:
            return False
        # Each prescribed step must have appeared, even if its SQL behavior was wrong.
        for step in reference.splitlines()[0].split():
            if not re.search(rf"^step {re.escape(step)}:", observed, re.MULTILINE):
                return False
        errors = re.findall(r"^ERROR:  SQLSTATE=(\w+)$", observed, re.MULTILINE)
        if any(code not in {"2BP01", "40P01", "XX000", "42704"} for code in errors):
            return False
        if any(
            line.startswith("ERROR:") and not line.startswith("ERROR:  SQLSTATE=")
            for line in observed.splitlines()
        ):
            return False
        if command.expected["tablespace-dependency-locking"] == "fail" and observed == reference:
            return False
    return True


def verify_preparation(case: dict[str, Any], curator: Path) -> None:
    """Do not trust editable preparation.json as proof of source or test identity."""
    for side, revision in (("parent", case["parent"]), ("fixed", case["fixed"])):
        source = curator / side
        if git(source, "rev-parse", "HEAD").decode().strip() != revision:
            raise ValueError("curator source revision mismatch")
        changed = set(git(source, "diff", "--name-only").decode().splitlines())
        untracked = set(
            git(source, "ls-files", "--others", "--exclude-standard").decode().splitlines()
        )
        if changed | untracked != (set(case["test_paths"]) if side == "parent" else set()):
            raise ValueError("curator worktree changed outside expected test patch")
    patch = test_patch(curator / "repository", case["parent"], case["fixed"], case["test_paths"])
    if hashlib.sha256(patch).hexdigest() != case["test_patch_sha256"]:
        raise ValueError("curator test patch identity mismatch")
    # Exact parent test contents must equal the fixed source, not merely changed filenames.
    for name in case["test_paths"]:
        if (curator / "parent" / name).read_bytes() != (curator / "fixed" / name).read_bytes():
            raise ValueError("curator test contents changed")


def qualify(
    case: dict[str, Any],
    curator: Path,
    output: Path,
    toolchains: list[Path],
    seconds: int = 7200,
    bundle: Path | None = None,
) -> dict[str, Any]:
    """Use the same bounded, sealed evaluator as candidate artifacts."""
    from benchmarks.large_projects.integration import qualify_integrated

    return qualify_integrated(case, curator, output, toolchains, seconds, bundle)


def prepare_set(case_ids: list[str], root: Path) -> list[dict[str, Any]]:
    """Prepare cases serially and preserve a receipt for every unsuccessful attempt."""
    cases = json.loads(CATALOG.read_text())["cases"]
    root.mkdir(parents=True, exist_ok=False)
    results = []
    for case in cases:
        if case["id"] not in case_ids:
            continue
        prepare_started = time.monotonic()
        try:
            results.append(prepare(case, root / case["id"]))
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            results.append(
                {
                    "case_id": case["id"],
                    "status": "environment_failure",
                    "error": str(exc),
                    "ready_for_model_comparison": False,
                }
            )
        results[-1]["source_preparation_seconds"] = time.monotonic() - prepare_started
        write_json(root / f"{case['id']}.json", results[-1])
    return results
