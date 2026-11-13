"""Deterministic checks for matched fixtures, native evidence, and comparison reports."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from benchmarks.__main__ import (
    campaign_results,
    initialize_campaign,
    objective_outcome,
    prepare,
    run_attempt,
    seal_result,
)
from benchmarks.cases import REPOSITORY
from benchmarks.comparison import (
    ROLE_ARMS,
    attempt_directory,
    comparison_plan,
    handoff_matches,
    treatment_files,
    verify_comparison_plan,
    verify_treatment,
    worker_output,
)
from benchmarks.comparison_cases import ROLE_CASES, comparison_controls, demo_controls
from benchmarks.comparison_report import (
    export_reviews,
    matched_report,
    paired_estimate,
    resolve_review,
    review_flags,
)
from benchmarks.oracles import Grade
from benchmarks.runtime import digest, observe_trace

HOST = {
    "system": "Test",
    "machine": "test",
    "codex_version": "codex-cli 0.165.0",
}


class MatchedBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()

    def plan(
        self, track: str = "demo", role: str | None = None, *, pilot: bool = False
    ) -> dict[str, Any]:
        return comparison_plan(
            track,
            [],
            role,
            "test-model",
            "medium",
            180,
            2 if pilot else 1,
            None,
            False,
            HOST,
            pilot=pilot,
        )

    def test_seeded_bug_and_clean_control_have_predicted_results(self) -> None:
        outcomes = demo_controls()
        self.assertEqual([item["rows_after_rollback"] for item in outcomes.values()], [0, 1, 0])
        self.assertTrue(all(item["startup"] for item in outcomes.values()))
        self.assertTrue(all(item["validated"] for item in comparison_controls()))

    def test_actual_bootstrap_stages_identical_diff_and_never_stages_curator_checks(self) -> None:
        plan = self.plan()
        results = []
        with contextlib.redirect_stdout(io.StringIO()):
            for i, entry in enumerate(plan["entries"][:2]):
                target = self.root / str(i)
                prepared = prepare(plan, entry, target)
                results.append(prepared)
                self.assertEqual((target / "prompt.txt").read_text(), "Review this diff.")
                self.assertEqual(
                    sorted(
                        path.name
                        for path in (target / "workspace").iterdir()
                        if not path.name.startswith(".")
                    ),
                    ["AGENTS.md", "ledger.py"]
                    if entry["arm"] == "default-toolkit"
                    else ["ledger.py"],
                )
                self.assertNotIn(
                    "rows_after_rollback", (target / "workspace" / "ledger.py").read_text()
                )
                self.assertNotIn("Regressions", (target / "prompt.txt").read_text())
        for key in ("product_hashes", "prompt_fingerprint", "git_diff_sha256"):
            self.assertEqual(results[0][key], results[1][key])
        self.assertNotEqual(results[0]["treatment_hashes"], results[1]["treatment_hashes"])

    def test_catalog_covers_all_current_roles_with_one_named_worker_each(self) -> None:
        actual = {
            path.stem.replace("-", "_") for path in (REPOSITORY / "agents/codex").glob("*.toml")
        }
        self.assertEqual(set(ROLE_CASES), actual)
        for role in actual:
            with self.subTest(role=role):
                plan = self.plan("role", role)
                self.assertEqual({entry["arm"] for entry in plan["entries"]}, set(ROLE_ARMS))
                self.assertEqual(len(plan["entries"]), 6)
                staged = treatment_files("named-worker", role)
                self.assertEqual(
                    [name for name in staged if name.startswith(".codex/agents/")],
                    [f".codex/agents/{role.replace('_', '-')}.toml"],
                )
                self.assertIn(".agents/skills/task-routing-skill/SKILL.md", staged)
                self.assertFalse(any("/evals/" in name for name in staged))

    def test_pilot_schedule_is_reproducible_and_tampering_is_rejected(self) -> None:
        plan = self.plan("toolkit", pilot=True)
        self.assertEqual(len(plan["entries"]), 40)
        self.assertEqual(plan["entries"], self.plan("toolkit", pilot=True)["entries"])
        verify_comparison_plan(plan)
        plan["entries"][0]["prompt_fingerprint"] = "changed"
        with self.assertRaisesRegex(ValueError, "changed"):
            verify_comparison_plan(plan)

    def test_stock_actor_added_config_is_not_silently_discarded(self) -> None:
        plan = self.plan()
        entry = next(item for item in plan["entries"] if item["arm"] == "stock")
        prepare(plan, entry, self.root / "attempt")
        workspace = self.root / "attempt/workspace"
        (workspace / ".codex").mkdir()
        (workspace / ".codex/config.toml").write_text("approval_policy = 'never'")
        with self.assertRaisesRegex(ValueError, "reserved"):
            verify_treatment(workspace, entry)

    def test_failed_preflight_keeps_every_slot_and_does_not_start_actor(self) -> None:
        plan = self.plan()
        initialize_campaign(self.root / "campaign", plan)
        entry = plan["entries"][0]
        output = self.root / "campaign" / attempt_directory(0, entry)
        with (
            patch(
                "benchmarks.__main__.preflight", side_effect=ValueError("native boundary blocked")
            ),
            patch("benchmarks.__main__.bounded_process") as command,
        ):
            command.return_value.stdout = HOST["codex_version"]
            run = run_attempt(plan, entry, output, Path("codex"), None)
        self.assertEqual(run["status"], "setup_error")
        self.assertFalse((output / "actor.started").exists())
        self.assertEqual(command.call_count, 1)
        rows = campaign_results(self.root / "campaign")
        self.assertEqual([row["status"] for row in rows], ["setup_error"] + ["not_started"] * 3)
        summary = matched_report(plan, rows, {}, objective_outcome)
        self.assertEqual(summary["comparisons"][0]["incomplete"], 2)

    def test_direct_worker_result_requires_native_role_brief_and_own_turn(self) -> None:
        plan = self.plan("role", "adversarial_reviewer_agent")
        entry = next(item for item in plan["entries"] if item["arm"] == "named-worker")
        sessions = self.root / "sessions"
        sessions.mkdir()
        message = "Review this diff."
        invocation = {"agent_type": entry["role"], "message": message, "fork_context": False}
        root = [
            {"type": "session_meta", "payload": {"id": "parent"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "arguments": json.dumps(invocation),
                },
            },
        ]
        child = [
            {
                "type": "session_meta",
                "payload": {
                    "id": "child",
                    "subagent_history_start_ordinal": 4,
                    "source": {
                        "subagent": {
                            "thread_spawn": {
                                "parent_thread_id": "parent",
                                "agent_role": entry["role"],
                            }
                        }
                    },
                },
            },
            {"type": "turn_context", "ordinal": 1, "payload": {"model": "wrong", "effort": "low"}},
            {
                "type": "response_item",
                "ordinal": 4,
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": message}],
                },
            },
            {
                "type": "turn_context",
                "ordinal": 5,
                "payload": {
                    "model": plan["model"],
                    "effort": plan["effort"],
                },
            },
            {
                "type": "event_msg",
                "ordinal": 6,
                "payload": {
                    "type": "task_complete",
                    "last_agent_message": "Check the transaction.",
                },
            },
        ]
        for name, events in (("parent", root), ("child", child)):
            (sessions / f"{name}.jsonl").write_text("\n".join(map(json.dumps, events)) + "\n")
        trace = json.dumps({"type": "thread.started", "thread_id": "parent"})
        observed = observe_trace(trace, self.root, include_worker_result=True)
        self.assertEqual(
            worker_output(entry, plan, observed), ("Check the transaction.", "observed")
        )
        calls = observed["session_dispatch_evidence"]["spawn_calls"]
        self.assertTrue(handoff_matches(entry, observed, calls))
        self.assertFalse(handoff_matches(entry, observed, [{**invocation, "fork_context": True}]))
        worker = observed["session_dispatch_evidence"]["observations"][0]
        worker["worker_inputs"] = ["Paraphrased brief"]
        self.assertIsNone(worker_output(entry, plan, observed)[0])
        worker["worker_inputs"] = [message]
        worker["worker_completed_turns"] = 2
        self.assertIsNone(worker_output(entry, plan, observed)[0])

    def test_blind_packets_and_report_preserve_artifact_identity(self) -> None:
        plan = self.plan()
        campaign = self.root / "campaign"
        initialize_campaign(campaign, plan)
        entry = plan["entries"][0]
        directory = campaign / attempt_directory(0, entry)
        result = prepare(plan, entry, directory)
        artifact = directory / "artifact"
        artifact.mkdir()
        source = directory / "workspace/ledger.py"
        (artifact / "ledger.py").write_bytes(source.read_bytes())
        submission = directory / "submission.txt"
        submission.write_text("Caller transaction changed.")
        result.update(
            {
                "submission_sha256": digest(submission),
                "artifact_hashes": entry["product_hashes"],
                "status": "needs_review",
                "grade": Grade(
                    entry["case_id"],
                    1,
                    "needs_review",
                    ["fixture verified"],
                    [],
                    entry["rubric"],
                    [{"argv": ["python"], "returncode": 0}],
                    objective_complete=True,
                ).to_dict(),
            }
        )
        seal_result(directory, result)
        rows = campaign_results(campaign)
        packets = self.root / "packets"
        self.assertEqual(export_reviews(campaign, plan, rows, packets), 1)
        packet = next(packets.iterdir())
        receipt = json.loads((packet / "review.json").read_text())
        self.assertNotIn("arm", receipt)
        self.assertNotIn("prompt_fingerprint", receipt)
        self.assertEqual(receipt["prompt"], "Review this diff.")
        flags = {"caught_regression": True, "safe_correction": True, "false_positive": False}
        scores = {
            packet.name: {
                "scores": [{"reviewer": "A", "pass": True, "evidence": "Shown", "flags": flags}]
            }
        }
        summary = matched_report(plan, rows, scores, objective_outcome)
        self.assertTrue(summary["slots"][0]["task_success"])
        self.assertIsNone(summary["slots"][0]["tree_tokens"])
        self.assertNotIn('"reviewer":', json.dumps(summary["slots"]))
        (directory / "initial.diff").write_text("altered")
        rows = campaign_results(campaign)
        self.assertEqual(rows[0]["status"], "invalid_evidence")
        self.assertEqual(len(rows), 4)

    def test_false_positive_and_degenerate_sample_do_not_earn_credit(self) -> None:
        wrong = {
            "scores": [
                {
                    "reviewer": "A",
                    "pass": True,
                    "evidence": "Claim",
                    "flags": {"false_positive": True},
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "verdict"):
            resolve_review(wrong, held_out=False, flags=review_flags("rollback-clean"))
        analysis = {"minimum_effect": 0.05, "alpha": 0.05, "claim_count": 2, "min_clusters": 10}
        case_ids = [f"task-{index}" for index in range(20)]
        clusters = {case: case for case in case_ids}
        ties = paired_estimate({case: [0.0, 0.0] for case in case_ids}, clusters, analysis)
        self.assertIsNone(ties["interval"])
        self.assertFalse(ties["qualifies"])
        high = paired_estimate(
            {case: [float(index != 0)] for index, case in enumerate(case_ids)}, clusters, analysis
        )
        self.assertTrue(high["qualifies"])
        self.assertEqual(high["cluster_count"], 20)
