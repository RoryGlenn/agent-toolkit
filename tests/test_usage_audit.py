"""Protect structural usage evidence and privacy with synthetic canonical traces."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import usage_audit as audit


def event(kind: str, **payload: object) -> dict[str, object]:
    """Make a canonical envelope, without a real conversation."""
    return {"type": kind, "payload": payload}


class UsageAuditTests(unittest.TestCase):
    """Verify evidence categories rather than cosmetic report formatting."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def trace(self, name: str, *events: dict[str, object]) -> Path:
        path = self.root / f"rollout-{name}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in events))
        return path

    def header(self, name: str = "root", **extra: object) -> dict[str, object]:
        return event("session_meta", id=name, source="cli", **extra)

    def child(self, name: str = "child", **extra: object) -> dict[str, object]:
        return event(
            "session_meta",
            id=name,
            source={
                "subagent": {
                    "thread_spawn": {
                        "parent_thread_id": "root",
                        "agent_role": "software_design_agent",
                    }
                }
            },
            **extra,
        )

    def complete(self) -> dict[str, object]:
        return event(
            "event_msg",
            type="task_complete",
            turn_id="turn-1",
            last_agent_message="PRIVATE OUTCOME",
        )

    def call(self, **extra: object) -> dict[str, object]:
        return event(
            "response_item",
            type="function_call",
            call_id="call-1",
            name="spawn_agent",
            arguments=json.dumps({"agent_type": "software_design_agent"}),
            **extra,
        )

    def test_aborted_ack_does_not_hide_actual_child_execution(self) -> None:
        root = self.trace(
            "root",
            self.header(),
            self.call(),
            event("response_item", type="function_call_output", call_id="call-1", output="aborted"),
        )
        child = self.trace("child", self.child(), self.complete())
        result = audit.audit(
            [root, child],
            [
                {
                    "case_id": "design",
                    "session_id": "root",
                    "expected_roles": ["software_design_agent"],
                }
            ],
            100_000,
        )
        self.assertEqual(result["cases"][0]["routing"], "observed")
        self.assertEqual(result["sessions"][0]["failed_role_acknowledgements"], 1)
        self.assertEqual(result["summary"]["named_roles_completed"], {"software_design_agent": 1})

    def test_acknowledged_spawn_is_not_actual_started_child(self) -> None:
        root = self.trace(
            "root",
            self.header(),
            self.call(),
            event(
                "response_item",
                type="function_call_output",
                call_id="call-1",
                output='{"task_name":"/root/design"}',
            ),
        )
        result = audit.audit(
            [root],
            [
                {
                    "case_id": "design",
                    "session_id": "root",
                    "expected_roles": ["software_design_agent"],
                    "checked_outcome": "passed",
                }
            ],
            100_000,
        )
        self.assertEqual(result["cases"][0]["routing"], "miss")
        self.assertEqual(result["cases"][0]["checked_outcome"], "passed")
        self.assertEqual(result["summary"]["named_roles_started"], {})

    def test_duplicate_call_events_count_once(self) -> None:
        path = self.trace("root", self.header(), self.call(), self.call())
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["tool_calls"], 1)
        self.assertEqual(row["role_attempts"], ["software_design_agent"])

    def test_parent_history_excluded_by_boundary(self) -> None:
        path = self.trace(
            "child",
            self.child(subagent_history_start_ordinal=4),
            self.call(),
            self.complete(),
            event("turn_context", model="parent-model"),
            event("turn_context", model="child-model"),
        )
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["tool_calls"], 0)
        self.assertEqual(row["completed_turns"], 0)
        self.assertEqual(row["models"], ["child-model"])

    def test_missing_boundary_does_not_attribute_inherited_history(self) -> None:
        path = self.trace(
            "child", self.child(history_base={"parent": "root"}), self.call(), self.complete()
        )
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertIn("inherited_history_boundary_unknown", row["limits"])
        self.assertEqual(row["completed_turns"], 0)

    def test_declared_surface_cannot_relabel_execution(self) -> None:
        """CLI, IDE, desktop, and unknown roots keep their observed identities."""
        for source, actual in [
            ("exec", "cli"),
            ("vscode", "ide"),
            ("desktop", "desktop"),
            ("future", "unknown"),
        ]:
            for declared in ["cli", "ide", "desktop"]:
                with self.subTest(source=source, declared=declared):
                    path = self.trace(
                        "root", event("session_meta", id="root", source=source), self.complete()
                    )
                    result = audit.audit(
                        [path],
                        [{"case_id": "surface", "surface": declared, "session_id": "root"}],
                        100_000,
                    )["cases"][0]
                    self.assertEqual(result["surface"], actual)
                    self.assertEqual(result["declared_surface"], declared)
                    expected = (
                        "incomplete_evidence"
                        if actual == "unknown"
                        else "observed"
                        if actual == declared
                        else "surface_mismatch"
                    )
                    self.assertEqual(result["routing"], expected)

    def test_missing_acknowledgement_is_reported_separately(self) -> None:
        path = self.trace("root", self.header(), self.call())
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["missing_role_acknowledgements"], 1)
        self.assertEqual(row["failed_role_acknowledgements"], 0)

    def test_inherited_parent_metadata_is_not_a_conflicting_child_header(self) -> None:
        """Current Codex puts the parent's header inside the inherited prefix."""
        path = self.trace(
            "child",
            self.child(subagent_history_start_ordinal=3),
            self.header(),
            self.call(),
            self.complete(),
        )
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["session_id"], "child")
        self.assertEqual(row["role"], "software_design_agent")
        self.assertEqual(row["role_attempts"], [])
        self.assertEqual(row["completed_turns"], 1)
        self.assertEqual(row["limits"], [])

    def test_same_session_header_is_idempotent_but_conflicting_header_is_unknown(self) -> None:
        path = self.trace("root", self.header(), self.header(), self.complete())
        self.assertEqual(audit.inspect_trace(path, set(), 100_000)["limits"], [])
        path = self.trace("conflict", self.header(), self.header("foreign"), self.complete())
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertIn("conflicting_session_metadata", row["limits"])
        self.assertEqual(row["completed_turns"], 0)

    def test_successful_skill_read_requires_actual_content_and_exit(self) -> None:
        call = event(
            "response_item",
            type="custom_tool_call",
            name="exec",
            call_id="read-1",
            input=(
                'await tools.exec_command({cmd:"cat '
                '/home/example/.agents/skills/software-design-skill/SKILL.md"});'
            ),
        )
        text = json.dumps(
            {
                "exit_code": 0,
                "output": "---\nname: software-design-skill\n---\nPRIVATE BOOK OR PROMPT",
            }
        )
        path = self.trace(
            "root",
            self.header(),
            call,
            event(
                "response_item",
                type="custom_tool_call_output",
                call_id="read-1",
                output=[{"type": "text", "text": text}],
            ),
        )
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        report = audit.audit([path], [], 100_000)
        self.assertEqual(
            report["sessions"][0]["skill_reads_observed"], {"software-design-skill": 1}
        )
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertNotIn("cat /home", json.dumps(report))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_read_failure_or_catalog_mention_is_not_a_skill_read(self) -> None:
        path = self.trace(
            "root",
            self.header(),
            event(
                "response_item",
                type="message",
                role="assistant",
                content=[{"text": "I used software-design-skill"}],
            ),
            event(
                "response_item",
                type="function_call",
                name="exec_command",
                call_id="read-1",
                arguments=json.dumps({"cmd": "cat /x/skills/software-design-skill/SKILL.md"}),
            ),
            event(
                "response_item",
                type="function_call_output",
                call_id="read-1",
                output=json.dumps({"exit_code": 1, "output": "No such file"}),
            ),
        )
        row = audit.inspect_trace(path, {"software-design-skill"}, 100_000)
        self.assertEqual(row["skill_read_attempts"], {"software-design-skill": 1})
        self.assertEqual(row["skill_reads_observed"], {})

    def test_read_file_envelope_supported(self) -> None:
        path = self.trace(
            "root",
            self.header(),
            event(
                "response_item",
                type="function_call",
                name="mcp__repository__read_file",
                call_id="read-1",
                arguments=json.dumps({"path": "skills/ddia-skill/SKILL.md"}),
            ),
            event(
                "response_item",
                type="function_call_output",
                call_id="read-1",
                output=[{"type": "text", "text": "---\nname: ddia-skill\n---\nGuidance"}],
            ),
        )
        row = audit.inspect_trace(path, {"ddia-skill"}, 100_000)
        self.assertEqual(row["skill_reads_observed"], {"ddia-skill": 1})

    def test_unknown_eligibility_is_not_a_miss(self) -> None:
        path = self.trace("root", self.header(), self.complete())
        report = audit.audit([path], [], 100_000)
        self.assertEqual(report["sessions"][0]["eligibility"], "unknown")
        self.assertEqual(report["cases"], [])
        self.assertNotIn("adoption_rate", report)

    def test_no_delegation_and_trivial_controls_detect_extra_work(self) -> None:
        path = self.trace("root", self.header(), self.call())
        cases = [
            {"case_id": "no-delegation", "session_id": "root", "forbid_delegation": True},
            {"case_id": "trivial", "session_id": "root", "require_no_tools": True},
        ]
        result = audit.audit([path], cases, 100_000)
        self.assertEqual(
            [c["routing"] for c in result["cases"]], ["unexpected_delegation", "unexpected_tools"]
        )

    def test_cli_stream_truncation_and_byte_limits_are_not_passes(self) -> None:
        path = self.root / "cli.jsonl"
        path.write_text('{"type":"thread.started","thread_id":"root"}\n{"broken":')
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertIn("cli_stream_not_canonical_rollout", row["limits"])
        self.assertEqual(row["malformed_lines"], 1)
        bounded = self.trace("large", self.header(), self.complete())
        row = audit.inspect_trace(bounded, set(), 10)
        self.assertEqual(row["hash_scope"], "inspected_prefix")
        self.assertIn("byte_or_line_limit", row["limits"])

    def test_running_followup_is_separate_from_completed_turn(self) -> None:
        path = self.trace(
            "child",
            self.child(),
            self.complete(),
            event("event_msg", type="task_started", turn_id="turn-2"),
        )
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["completed_turns"], 1)
        self.assertEqual(row["unclosed_turns"], 1)

    def test_aborted_turn_is_terminal_but_not_a_successful_completion(self) -> None:
        path = self.trace(
            "child",
            self.child(),
            event("event_msg", type="task_started", turn_id="turn-1"),
            event("event_msg", type="turn_aborted", turn_id="turn-1"),
        )
        row = audit.inspect_trace(path, set(), 100_000)
        self.assertEqual(row["completed_turns"], 0)
        self.assertEqual(row["aborted_turns"], 1)
        self.assertEqual(row["unclosed_turns"], 0)

    def test_unreadable_trace_and_missing_surface_are_explicit(self) -> None:
        report = audit.audit(
            [self.root / "missing"],
            [
                {
                    "case_id": "desktop",
                    "surface": "desktop",
                    "skip_reason": "ui_controls_unavailable",
                }
            ],
            100_000,
        )
        self.assertIn("unreadable_trace", report["sessions"][0]["limits"])
        self.assertEqual(report["cases"][0]["routing"], "skipped")
        self.assertEqual(report["cases"][0]["checked_outcome"], "not_checked")

    def test_cli_emits_content_free_error_on_bad_input(self) -> None:
        path = self.root / "manifest.json"
        path.write_text('{"cases": "PRIVATE"}')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = audit.main(["--manifest", str(path)])
        self.assertEqual(code, 2)
        self.assertNotIn("PRIVATE", out.getvalue())

    def test_nonobject_manifest_and_symlink_are_rejected_without_content(self) -> None:
        """Bad JSON shapes return a short error and explicit links are not followed."""
        path = self.root / "manifest.json"
        path.write_text('["PRIVATE"]')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(["--manifest", str(path)]), 2)
        target = self.trace("target", self.header())
        link = self.root / "link.jsonl"
        link.symlink_to(target)
        self.assertIn("unreadable_trace", audit.inspect_trace(link, set(), 100_000)["limits"])


if __name__ == "__main__":
    unittest.main()
