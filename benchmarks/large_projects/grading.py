"""Fail-closed interpretation of upstream control output, never candidate prose."""

from __future__ import annotations

import json
import re
from typing import Any

from benchmarks.process import Execution


def classify(result: Execution, checks: dict[str, str], expected: dict[str, str]) -> str:
    """Require exact discovery, terminal outcomes and expected behavioral failures."""
    if result.timed_out or result.output_limited or result.returncode < 0:
        return "environment_failure"
    if not expected or set(checks) != set(expected):
        return "environment_failure"
    if any(value not in ("pass", "fail") for value in checks.values()):
        return "environment_failure"
    failures = any(value == "fail" for value in checks.values())
    if result.returncode != (1 if failures else 0):
        return "environment_failure"
    return "qualified" if checks == expected else "behavior_mismatch"


def go_checks(
    output: str, names: list[str], *, allow_detected_deadlock: bool = False
) -> dict[str, str]:
    """Require terminal results for every discovered test, including descendants.

    Go's deterministic synctest deadlock can abort a child before its terminal event.
    That exception is opt-in only for the known failing cancellation control, never a timeout.
    """
    checks: dict[str, str] = {}
    discovered: set[str] = set()
    terminal: dict[str, str] = {}
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        name, action = event.get("Test"), event.get("Action")
        if not isinstance(name, str):
            continue
        roots = [root for root in names if name == root or name.startswith(root + "/")]
        if not roots:
            continue
        if action == "run":
            if name in discovered:
                return {}
            discovered.add(name)
        if action in ("pass", "fail", "skip"):
            if name in terminal:
                return {}
            terminal[name] = action
    for root in names:
        children = {name for name in discovered if name == root or name.startswith(root + "/")}
        if root not in discovered or root not in terminal:
            return {}
        missing = children - terminal.keys()
        if missing and not (
            allow_detected_deadlock
            and terminal[root] == "fail"
            and "panic: deadlock: all goroutines in bubble are blocked" in output
        ):
            return {}
        state = terminal[root]
        if any(terminal.get(name) == "skip" for name in children):
            state = "skip"
        checks[root] = state
    return checks


def python_checks(output: str, names: list[str]) -> dict[str, str]:
    """Read the controller-injected unittest receipt, including skips and errors."""
    for line in reversed(output.splitlines()):
        if line.startswith("TOOLKIT_TESTS="):
            data: Any = json.loads(line.removeprefix("TOOLKIT_TESTS="))
            if isinstance(data, dict) and set(data) <= set(names):
                return dict(data)
    return {}


def mocha_checks(output: str) -> dict[str, int]:
    """Require the browser harness summary; no inferred success from exit zero."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", output)
    counts = {}
    for label in ("passing", "failing", "pending"):
        values = re.findall(rf"^\s*(\d+) {label}\b", clean, re.MULTILINE)
        if len(values) > 1:
            return {}
        counts[label] = int(values[0]) if values else 0
    return counts if counts.get("passing") else {}


def browser_checks(output: str) -> tuple[dict[str, int], dict[str, str]]:
    """Parse Mocha's JSON reporter, including exact discovered names and pending tests."""
    for match in re.finditer(r"^\s*\{", output, re.MULTILINE):
        try:
            value, _ = json.JSONDecoder().raw_decode(output[match.end() - 1 :])
        except ValueError:
            continue
        if not isinstance(value, dict) or "stats" not in value:
            continue
        checks = {}
        for key, state in (("passes", "pass"), ("failures", "fail"), ("pending", "skip")):
            for test in value.get(key, []):
                name = test.get("title")
                if not isinstance(name, str) or name in checks:
                    return {}, {}
                checks[name] = state
        stats = value["stats"]
        if stats.get("tests") != len(checks):
            return {}, {}
        counts = {
            "passing": sum(v == "pass" for v in checks.values()),
            "failing": sum(v == "fail" for v in checks.values()),
            "pending": sum(v == "skip" for v in checks.values()),
        }
        return counts, checks
    return {}, {}
