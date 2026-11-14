"""Shared CLI/runtime contracts for large projects and matched comparisons."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import benchmarks.__main__ as cli
from benchmarks.large_projects.artifacts import tree_hashes
from benchmarks.process import Execution
from benchmarks.runtime import config_text


class MainIntegrationTests(unittest.TestCase):
    def plan(self, attempts: int = 1) -> dict:
        return cli.make_plan(
            ["ddia-easy"],
            ["baseline"],
            "unused",
            "high",
            "downloaded",
            60,
            attempts,
            None,
            "controlled",
            None,
        )

    def test_matched_v1_and_large_v2_runtime_profiles_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            paths = [root / name for name in ("workspace", "actor", "client", "tmp")]
            common = (*paths, "unused", "high")
            matched = tomllib.loads(
                config_text(
                    *common,
                    project_instructions=True,
                    writable=False,
                    agents_enabled=False,
                    max_children=1,
                    readonly=[root / "matched-input"],
                    instructions="controlled coordinator",
                )
            )
            self.assertTrue(matched["features"]["multi_agent"])
            self.assertFalse(matched["features"]["multi_agent_v2"])
            self.assertFalse(matched["features"]["code_mode"])
            self.assertFalse(matched["agents"]["enabled"])
            self.assertEqual(matched["agents"]["max_concurrent_threads_per_session"], 1)
            self.assertEqual(matched["developer_instructions"], "controlled coordinator")
            self.assertEqual(matched["project_doc_max_bytes"], 32768)
            permissions = matched["permissions"]["benchmark"]
            self.assertEqual(permissions["filesystem"][str(paths[0])], "read")
            self.assertEqual(permissions["filesystem"][str(paths[3])], "write")
            self.assertFalse(permissions["network"]["enabled"])
            large = tomllib.loads(
                config_text(
                    *common,
                    project_guidance=True,
                    local_network=True,
                    readonly=[root / "matched-input"],
                    readonly_extra=[root / "large-input"],
                    shell_environment={"GOMAXPROCS": "2"},
                )
            )
            self.assertTrue(large["features"]["multi_agent_v2"])
            self.assertTrue(large["features"]["code_mode"])
            self.assertEqual(large["project_doc_max_bytes"], 32768)
            self.assertEqual(large["shell_environment_policy"]["set"]["GOMAXPROCS"], "2")
            filesystem = large["permissions"]["benchmark"]["filesystem"]
            for name in ("matched-input", "large-input"):
                self.assertEqual(filesystem[str(root / name)], "read")
            domains = large["permissions"]["benchmark"]["network"]["domains"]
            self.assertEqual(domains, {"localhost": "allow", "127.0.0.1": "allow"})
            with self.assertRaisesRegex(ValueError, "cannot be combined"):
                config_text(*common, local_network=True, project_instructions=True)

    def test_prompt_inspection_uses_the_injected_cell_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            executor = SimpleNamespace(codex=Path("codex"), workspace=root, environment={})
            output = [
                {
                    "tools": [
                        {
                            "name": "functions",
                            "type": "namespace",
                            "tools": [{"name": "exec", "description": "### `exec_command`"}],
                        }
                    ]
                }
            ]
            runner = Mock(return_value=Execution([], 0, json.dumps(output), "", 0))
            with patch.object(cli, "bounded_process", side_effect=AssertionError("host execution")):
                receipt = cli.verify_prompt_surface(executor, root, run=runner)
            self.assertIn("functions.exec", receipt["exposed_tools"])
            self.assertEqual(runner.call_args.args[0][-1], "Read TASK.md.")
            self.assertEqual(json.loads((root / "prompt-surface.json").read_text()), output)

    def test_large_artifact_reconciliation_uses_the_frozen_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            artifact = root / "artifact"
            artifact.mkdir()
            (artifact / "changes.json").write_text("{}")
            plan = self.plan()
            entry = plan["entries"][0]
            expected = {
                **plan,
                **entry,
                "large_context": {"case": "fixture"},
                "planned_arms": ["baseline"],
            }
            result = {
                **cli.attempt_metadata(plan, entry),
                "status": "failed",
                "artifact_hashes": tree_hashes(artifact),
            }
            cli.seal_result(root, result)
            self.assertEqual(
                cli.read_attempt(root, expected, entry, matched=False)["status"], "failed"
            )
            (artifact / "changes.json").write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, "artifact changed"):
                cli.read_attempt(root, expected, entry, matched=False)

    def test_campaign_cancellation_retains_report_and_stops_later_slots(self) -> None:
        plan = self.plan(attempts=2)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "campaign"

            def cancelled(plan, entry, root, _codex, _auth):
                root.mkdir()
                result = {
                    **cli.attempt_metadata(plan, entry),
                    "status": "cancelled",
                    "operator_cancelled": True,
                }
                cli.seal_result(root, result)
                return result

            with (
                patch.object(cli, "read_plan", return_value=plan),
                patch.object(cli, "resolve_codex", return_value=Path("unused")),
                patch.object(cli, "run_attempt", side_effect=cancelled) as attempt,
                patch.object(sys, "argv", ["benchmarks", "run", "unused", "--output", str(output)]),
                redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit) as stopped,
            ):
                cli.main()
            self.assertEqual(stopped.exception.code, 130)
            self.assertEqual(attempt.call_count, 1)
            self.assertTrue((output / "report.json").is_file())
            self.assertEqual(
                [row["status"] for row in cli.campaign_results(output)],
                ["cancelled", "not_started"],
            )

    def test_matched_plan_rejects_a_large_project_context_before_setup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "plan.json"
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "benchmarks",
                        "plan",
                        "--comparison",
                        "toolkit",
                        "--large-context",
                        "unused",
                        "--model",
                        "unused",
                        "--output",
                        str(output),
                    ],
                ),
                patch.object(cli, "resolve_codex") as resolve,
                redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as stopped,
            ):
                cli.main()
            self.assertEqual(stopped.exception.code, 2)
            resolve.assert_not_called()
            self.assertFalse(output.exists())
