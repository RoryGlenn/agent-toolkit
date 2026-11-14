#!/usr/bin/env python3
"""Inspect bounded local Codex rollout evidence without exporting conversations."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shlex
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import install

ROOT = Path(__file__).resolve().parent
ROLES = {
    name.removesuffix(".toml").replace("-", "_")
    for names in install.AGENTS["codex"].values()
    for name in names
}
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
MODEL = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
SKILL_PATH = re.compile(r"(?:^|[/~])(?:\.agents/)?skills/([a-z0-9-]+)/SKILL\.md\b")
MAX_LINE = 8 * 1024 * 1024
MAX_DISCOVERY = 20_000


def identifier(value: Any) -> str | None:
    """Return only bounded opaque IDs, never arbitrary metadata text."""
    return value if isinstance(value, str) and IDENTIFIER.fullmatch(value) else None


def output_text(value: Any) -> str:
    """Flatten tool output in memory; callers never put this text in reports."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(output_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(
            output_text(value[key]) for key in ("text", "content", "output") if key in value
        )
    return ""


def arguments(value: Any) -> dict[str, Any]:
    """Decode structured arguments without evaluating trace code."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (ValueError, RecursionError):
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def read_targets(name: str, value: Any, skills: set[str]) -> set[str]:
    """Recognize read tools and a conservative subset of direct shell reads."""
    data = arguments(value)
    candidates: list[str] = []
    if name.endswith("read_file") or name.endswith("read_text_file"):
        path = data.get("path")
        if isinstance(path, str):
            candidates.append(path)
    commands: list[str] = []
    for key in ("cmd", "command"):
        if isinstance(data.get(key), str):
            commands.append(data[key])
    if name == "exec" and isinstance(value, str):
        for match in re.finditer(r"\bcmd\s*:\s*(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", value):
            try:
                command = ast.literal_eval(match[1])
            except (ValueError, SyntaxError):
                continue
            if isinstance(command, str):
                commands.append(command)
    for command in commands:
        for match in re.finditer(
            r"(?:^|[;&|\n])\s*(?:/bin/)?(?:cat|head|tail|sed)\s+([^;&|\n]+)", command
        ):
            try:
                candidates.extend(shlex.split(match[1]))
            except ValueError:
                pass
    return {
        match[1] for text in candidates for match in SKILL_PATH.finditer(text) if match[1] in skills
    }


def successful_read(output: Any, skill: str, tool: str) -> bool:
    """Require matching skill content and a successful identifiable tool result."""
    text = output_text(output)
    normalized = text.replace('\\"', '"').replace("\\n", "\n")
    if not re.search(rf"(?:^|\n)\s*name:\s*['\"]?{re.escape(skill)}(?:['\"]|\s|$)", normalized):
        return False
    if re.search(r'"(?:isError|is_error)"\s*:\s*true', normalized):
        return False
    codes = re.findall(r'"exit_code"\s*:\s*(-?\d+)', normalized)
    codes += re.findall(r"Process exited with code (\d+)", normalized)
    if codes:
        return all(code == "0" for code in codes)
    return tool.endswith("read_file") or tool.endswith("read_text_file")


def inspect_trace(path: Path, skills: set[str], max_bytes: int) -> dict[str, Any]:
    """Project supported canonical events into content-free evidence."""
    record: dict[str, Any] = {
        "session_id": None,
        "parent_id": None,
        "role": None,
        "surface": "unknown",
        "models": [],
        "completed_turns": 0,
        "aborted_turns": 0,
        "unclosed_turns": 0,
        "tool_calls": 0,
        "skill_read_attempts": {},
        "skill_reads_observed": {},
        "role_attempts": [],
        "failed_role_acknowledgements": 0,
        "missing_role_acknowledgements": 0,
        "limits": [],
    }
    calls: dict[str, tuple[str, set[str], str | None]] = {}
    results: dict[str, Any] = {}
    starts: set[str] = set()
    completed: set[str] = set()
    aborted: set[str] = set()
    metadata_seen = False
    boundary = 1
    own_history_known = True
    digest = hashlib.sha256()
    total = 0
    malformed = 0
    try:
        if not path.is_file() or path.is_symlink():
            raise OSError("not a regular selected trace")
        with path.open("rb") as stream:
            for ordinal in range(1, 1_000_001):
                line = stream.readline(min(MAX_LINE + 1, max_bytes - total + 1))
                if not line:
                    break
                if total + len(line) > max_bytes or len(line) > MAX_LINE:
                    record["limits"].append("byte_or_line_limit")
                    break
                digest.update(line)
                total += len(line)
                try:
                    event = json.loads(line)
                except (ValueError, RecursionError):
                    malformed += 1
                    continue
                if not isinstance(event, dict):
                    malformed += 1
                    continue
                kind, payload = event.get("type"), event.get("payload")
                if not isinstance(payload, dict):
                    if kind in {"thread.started", "item.completed", "turn.completed"}:
                        if "cli_stream_not_canonical_rollout" not in record["limits"]:
                            record["limits"].append("cli_stream_not_canonical_rollout")
                    continue
                if kind == "session_meta":
                    if metadata_seen:
                        event_ordinal = event.get("ordinal")
                        position = event_ordinal if type(event_ordinal) is int else ordinal - 1
                        if position < boundary:
                            continue
                        if identifier(payload.get("id")) != record["session_id"]:
                            record["limits"].append("conflicting_session_metadata")
                            own_history_known = False
                        continue
                    metadata_seen = True
                    record["session_id"] = identifier(payload.get("id"))
                    source = payload.get("source")
                    if isinstance(source, str):
                        record["surface"] = {
                            "cli": "cli",
                            "exec": "cli",
                            "vscode": "ide",
                            "desktop": "desktop",
                        }.get(source, "unknown")
                    subagent = source.get("subagent", {}) if isinstance(source, dict) else {}
                    spawn = subagent.get("thread_spawn", {}) if isinstance(subagent, dict) else {}
                    if isinstance(spawn, dict) and spawn:
                        record["parent_id"] = identifier(spawn.get("parent_thread_id"))
                        role = spawn.get("agent_role")
                        record["role"] = role if role in ROLES else "other"
                        record["surface"] = "subagent"
                        start = payload.get("subagent_history_start_ordinal")
                        if type(start) is int and start >= 1:
                            boundary = start
                        elif payload.get("history_base") is not None:
                            own_history_known = False
                            record["limits"].append("inherited_history_boundary_unknown")
                    continue
                event_ordinal = event.get("ordinal")
                position = event_ordinal if type(event_ordinal) is int else ordinal - 1
                if not metadata_seen or not own_history_known or position < boundary:
                    continue
                if kind == "turn_context":
                    model = payload.get("model")
                    if (
                        isinstance(model, str)
                        and MODEL.fullmatch(model)
                        and model not in record["models"]
                    ):
                        record["models"].append(model)
                if kind == "event_msg":
                    event_type = payload.get("type")
                    turn = identifier(payload.get("turn_id"))
                    if event_type == "task_started" and turn:
                        starts.add(turn)
                    if event_type in {"turn_aborted", "task_aborted"} and turn:
                        aborted.add(turn)
                    if (
                        event_type in {"task_complete", "turn_complete"}
                        and payload.get("error") is None
                        and turn
                    ):
                        completed.add(turn)
                if kind != "response_item":
                    continue
                item_type = payload.get("type")
                call_id = identifier(payload.get("call_id"))
                if item_type in {"function_call", "custom_tool_call"} and call_id:
                    name = payload.get("name")
                    if not isinstance(name, str):
                        continue
                    value = payload.get("arguments", payload.get("input"))
                    targets = read_targets(name, value, skills)
                    role = None
                    if name.endswith("spawn_agent"):
                        selected = arguments(value).get("agent_type")
                        role = selected if selected in ROLES else "other"
                    calls.setdefault(call_id, (name, targets, role))
                if item_type in {"function_call_output", "custom_tool_call_output"} and call_id:
                    results[call_id] = payload.get("output")
            else:
                record["limits"].append("event_limit")
    except OSError:
        record["limits"].append("unreadable_trace")
    if not metadata_seen or record["session_id"] is None:
        record["limits"].append("missing_valid_session_metadata")
    if malformed:
        record["limits"].append("malformed_lines")
    record["malformed_lines"] = malformed
    attempts: Counter[str] = Counter()
    reads: Counter[str] = Counter()
    roles: list[str] = []
    for call_id, (name, targets, role) in calls.items():
        for target in targets:
            attempts[target] += 1
            if call_id in results and successful_read(results[call_id], target, name):
                reads[target] += 1
        if role:
            roles.append(role)
            if call_id not in results:
                record["missing_role_acknowledgements"] += 1
            result_text = output_text(results.get(call_id)).lower()
            if any(
                word in result_text for word in ('"error"', "aborted", "not found", "unavailable")
            ):
                record["failed_role_acknowledgements"] += 1
    record.update(
        {
            "tool_calls": len(calls),
            "skill_read_attempts": dict(sorted(attempts.items())),
            "skill_reads_observed": dict(sorted(reads.items())),
            "role_attempts": roles,
            "completed_turns": len(completed),
            "aborted_turns": len(aborted),
            "unclosed_turns": len(starts - completed - aborted),
            "sha256": digest.hexdigest(),
            "inspected_bytes": total,
            "hash_scope": "inspected_prefix"
            if "byte_or_line_limit" in record["limits"]
            else "full_trace",
            "eligibility": "unknown",
        }
    )
    return record


def evaluate_cases(
    traces: list[dict[str, Any]], cases: list[dict[str, Any]], skills: set[str]
) -> list[dict[str, Any]]:
    """Apply explicit expectations without inferring eligibility from prose."""
    by_id = {row["session_id"]: row for row in traces if row["session_id"]}
    output = []
    for case in cases:
        case_id = identifier(case.get("case_id"))
        if not case_id:
            raise ValueError("Each case requires a bounded case_id.")
        expected = case.get("expected_roles", [])
        if not isinstance(expected, list) or any(role not in ROLES for role in expected):
            raise ValueError("Case expected_roles must contain known toolkit roles.")
        expected_skills = case.get("expected_skills", [])
        if not isinstance(expected_skills, list) or any(
            skill not in skills for skill in expected_skills
        ):
            raise ValueError("Case expected_skills must contain known skill names.")
        parent = by_id.get(case.get("session_id"))
        declared_surface = case.get("surface")
        if declared_surface not in {None, "cli", "ide", "desktop"}:
            raise ValueError("Unknown declared surface.")
        observed_surface = parent["surface"] if parent else "unknown"
        surface_check = (
            "not_declared"
            if declared_surface is None
            else "unknown"
            if observed_surface == "unknown"
            else "matched"
            if declared_surface == observed_surface
            else "mismatch"
        )
        children = [row for row in traces if parent and row["parent_id"] == parent["session_id"]]
        descendants = list(children)
        for _ in range(8):
            parents = {row["session_id"] for row in descendants}
            additions = [
                row for row in traces if row["parent_id"] in parents and row not in descendants
            ]
            if not additions:
                break
            descendants.extend(additions)
        started = sorted({row["role"] for row in descendants if row["role"] in ROLES})
        finished = sorted(
            {
                row["role"]
                for row in descendants
                if row["role"] in ROLES and row["completed_turns"] > 0
            }
        )
        limited = not parent or bool(parent["limits"]) or any(row["limits"] for row in descendants)
        missing = sorted(set(expected) - set(finished))
        accessed = sorted(
            {
                skill
                for row in ([parent] if parent else []) + descendants
                for skill in row["skill_reads_observed"]
            }
        )
        missing_skills = sorted(set(expected_skills) - set(accessed))
        routing = "incomplete_evidence" if limited else "observed" if not missing else "miss"
        if surface_check == "mismatch":
            routing = "surface_mismatch"
        elif surface_check == "unknown":
            routing = "incomplete_evidence"
        if case.get("forbid_delegation") and (children or (parent and parent["role_attempts"])):
            routing = "unexpected_delegation"
        if case.get("require_no_tools") and parent and parent["tool_calls"]:
            routing = "unexpected_tools"
        skip = case.get("skip_reason")
        if skip not in {None, "ui_controls_unavailable", "surface_not_installed"}:
            raise ValueError("Unknown case skip_reason.")
        if skip:
            routing = "skipped"
        outcome = case.get("checked_outcome", "not_checked")
        if outcome not in {"passed", "failed", "not_checked"}:
            raise ValueError("Unknown checked_outcome.")
        if skip and outcome != "not_checked":
            raise ValueError("An unexecuted surface cannot have a checked outcome.")
        output.append(
            {
                "case_id": case_id,
                "surface": observed_surface,
                "declared_surface": declared_surface,
                "surface_check": surface_check,
                "routing": routing,
                "expected_roles": expected,
                "roles_started": started,
                "roles_completed": finished,
                "missing_completed_roles": missing,
                "skills_read": accessed,
                "missing_skill_reads": missing_skills,
                "checked_outcome": outcome,
                "skip_reason": skip,
            }
        )
    return output


def audit(paths: list[Path], cases: list[dict[str, Any]], max_bytes: int) -> dict[str, Any]:
    """Return only aggregate metadata and content-free per-session evidence."""
    skills = set(install.inventory(ROOT)) | {"doc-agent"}
    traces = [inspect_trace(path, skills, max_bytes) for path in dict.fromkeys(paths)]
    seen: set[str] = set()
    for trace in traces:
        session_id = trace["session_id"]
        if session_id and session_id in seen:
            trace["limits"].append("duplicate_session_identity")
        if session_id:
            seen.add(session_id)
    case_results = evaluate_cases(traces, cases, skills)
    declared = {case.get("session_id") for case in cases}
    for row in traces:
        row["eligibility"] = (
            "declared_verification_case"
            if row["session_id"] is not None and row["session_id"] in declared
            else "subagent_observation"
            if row["parent_id"]
            else "unknown"
        )
    starts: Counter[str] = Counter()
    completions: Counter[str] = Counter()
    for row in traces:
        if row["parent_id"] and row["role"] in ROLES:
            starts[row["role"]] += 1
            if row["completed_turns"]:
                completions[row["role"]] += 1
    return {
        "schema_version": 1,
        "scope": "bounded_local_evidence",
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "summary": {
            "traces_inspected": len(traces),
            "traces_with_limits": sum(bool(t["limits"]) for t in traces),
            "eligibility_unclassified": sum(row["eligibility"] == "unknown" for row in traces),
            "named_roles_started": dict(sorted(starts.items())),
            "named_roles_completed": dict(sorted(completions.items())),
        },
        "cases": case_results,
        "sessions": traces,
        "limits": [
            "Undeclared task eligibility is unknown.",
            "Skill access is not proof of application or result quality.",
            "Completed children are not independent outcome validation.",
            "Unclosed turn records do not establish that a worker is currently running.",
            "Bounded smoke evidence does not establish universal adoption or untested UI behavior.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """Print a local evidence report; never mutate traces or create a schedule."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-root", type=Path, default=Path.home() / ".codex/sessions")
    parser.add_argument(
        "--trace",
        action="append",
        type=Path,
        default=[],
        help="Inspect an exact canonical rollout; repeatable.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Local JSON object with a cases array of explicit expectations.",
    )
    parser.add_argument("--max-sessions", type=int, default=100)
    parser.add_argument("--since-hours", type=float, default=24)
    parser.add_argument(
        "--max-bytes", type=int, default=32 * 1024 * 1024, help="Maximum inspected bytes per trace."
    )
    args = parser.parse_args(argv)
    try:
        if (
            not 1 <= args.max_sessions <= 500
            or not 0 < args.since_hours <= 8760
            or not 1 <= args.max_bytes <= 128 * 1024 * 1024
        ):
            raise ValueError("Session, time, or byte bound is outside the supported range.")
        cases: list[dict[str, Any]] = []
        if args.manifest:
            manifest = json.loads(args.manifest.read_text())
            if not isinstance(manifest, dict):
                raise ValueError("Manifest must be an object.")
            raw_cases = manifest.get("cases")
            if not isinstance(raw_cases, list) or not all(
                isinstance(case, dict) for case in raw_cases
            ):
                raise ValueError("Manifest must contain a cases array of objects.")
            cases = raw_cases
        paths = args.trace
        discovery_limited = False
        if not paths:
            cutoff = (datetime.now(UTC) - timedelta(hours=args.since_hours)).timestamp()
            if not args.session_root.is_dir():
                raise ValueError("Session root is not a readable directory.")
            candidates = []
            for index, path in enumerate(args.session_root.rglob("rollout-*.jsonl")):
                if index >= MAX_DISCOVERY:
                    discovery_limited = True
                    break
                if path.is_file() and not path.is_symlink() and path.stat().st_mtime >= cutoff:
                    candidates.append(path)
            paths = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[
                : args.max_sessions
            ]
        if len(paths) > args.max_sessions:
            raise ValueError("Explicit trace selection exceeds --max-sessions.")
        report = audit(paths, cases, args.max_bytes)
        report["selection"] = {
            "max_sessions": args.max_sessions,
            "since_hours": args.since_hours,
            "max_bytes_per_trace": args.max_bytes,
            "discovery_limited": discovery_limited,
            "explicit_traces": bool(args.trace),
        }
        print(json.dumps(report, indent=2))
        return (
            0
            if not discovery_limited
            and not report["summary"]["traces_with_limits"]
            and all(
                c["routing"] in {"observed", "skipped"}
                and c["checked_outcome"] != "failed"
                and (not c["missing_skill_reads"] or c["routing"] == "skipped")
                for c in report["cases"]
            )
            else 1
        )
    except (OSError, ValueError, TypeError, RecursionError):
        print(
            json.dumps({"schema_version": 1, "error": "Invalid or unreadable local audit input."})
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
