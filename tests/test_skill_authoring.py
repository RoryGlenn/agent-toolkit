"""Test upstream tools and the Codex adapter using newly created, disposable skills."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from skill_authoring import ROOT, UPSTREAM, native, workflow


class SkillAuthoringTests(unittest.TestCase):
    """Check real upstream integration and independent actor/grader data boundaries."""

    def setUp(self) -> None:
        """Create a new fixture skill; no existing toolkit skill or role is used."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.skill = self.root / "fixture-skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text(
            "---\nname: fixture-skill\ndescription: Transform fixture inputs.\n---\n"
            "Write the selected fixture result to outputs/result.txt.\n"
        )
        (self.skill / "inputs").mkdir()
        (self.skill / "inputs/source.txt").write_text("source-data")
        (self.skill / "evals").mkdir()
        (self.skill / "evals/answers.txt").write_text("private-answer")
        self.evals = self.skill / "evals/evals.json"
        self.data: dict[str, Any] = {
            "skill_name": "fixture-skill",
            "evals": [
                {
                    "id": 1,
                    "prompt": "Transform inputs/source.txt.",
                    "expected_output": "private expected outcome",
                    "files": ["inputs/source.txt"],
                    "expectations": ["Result matches the fixture."],
                }
            ],
        }
        self.evals.write_text(json.dumps(self.data))
        self.auth = self.root / "fixture-auth.json"
        self.auth.write_text('{"fixture":true}')
        self.output = self.root / "iteration-1"

    def execute_fixture(
        self,
        command: list[str],
        cwd: Path,
        environment: dict[str, str],
        text: str = "",
        seconds: int = 30,
    ) -> dict[str, Any]:
        """Simulate a Codex protocol response while checking the staged actor surface."""
        self.assertEqual((cwd / "inputs/source.txt").read_text(), "source-data")
        self.assertFalse((cwd / "evals").exists())
        self.assertNotIn("private expected outcome", text)
        self.assertNotIn("Result matches the fixture.", text)
        self.assertNotIn("private-answer", text)
        home = Path(environment["HOME"])
        candidate = home / ".agents/skills/fixture-skill"
        self.assertFalse((candidate / "evals").exists())
        self.assertFalse((candidate / "agents/grader.md").exists())
        self.assertEqual(Path(environment["CODEX_HOME"]).parent, cwd.parent)
        (cwd / "outputs").mkdir()
        (cwd / "outputs/result.txt").write_text("result")
        Path(command[command.index("-o") + 1]).write_text("Fixture completed.")
        return {
            "returncode": 0,
            "timed_out": False,
            "output_limited": False,
            "stdout": json.dumps(
                {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}
            ),
            "stderr": "",
            "total_duration_seconds": 0.25,
        }

    def run_fixture(self, repetitions: int = 1) -> dict[str, Any]:
        """Run the real campaign orchestration with a simulated model and isolation result."""
        with (
            patch.object(native, "preflight", return_value={"fixture_only": True}),
            patch.object(native, "execute", side_effect=self.execute_fixture),
        ):
            return workflow.run(
                self.evals,
                self.skill,
                self.output,
                Path(sys.executable).resolve(),
                self.auth,
                "fixture-model",
                "medium",
                repetitions,
                5,
            )

    def grade_fixture(self, plan: dict[str, Any]) -> None:
        """Write independently checkable fixture grades in Anthropic's actual schema."""
        for relative in plan["runs"]:
            passed = "/with_skill/" in relative
            workflow.write_json(
                self.output / relative / "grading.json",
                {
                    "expectations": [
                        {
                            "text": "Result matches the fixture.",
                            "passed": passed,
                            "evidence": "Fixture oracle inspected result.txt.",
                        }
                    ],
                    "summary": {
                        "passed": int(passed),
                        "failed": int(not passed),
                        "total": 1,
                        "pass_rate": float(passed),
                    },
                    "timing": {"total_duration_seconds": 999},
                    "execution_metrics": {"output_chars": 777},
                },
            )

    def test_native_scaffold_and_validation_are_upstream(self) -> None:
        """Execute the native generator, including UI metadata and unfinished-draft rejection."""
        command = [
            sys.executable,
            "-m",
            "skill_authoring",
            "scaffold",
            "fresh-skill",
            "--path",
            str(self.root),
        ]
        result = subprocess.run(
            command, cwd=ROOT.parent, capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        created = self.root / "fresh-skill"
        self.assertTrue((created / "agents/openai.yaml").is_file())
        invalid = subprocess.run(
            [sys.executable, "-m", "skill_authoring", "validate", str(created)],
            cwd=ROOT.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(invalid.returncode, 1)
        retry = subprocess.run(command, cwd=ROOT.parent, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(retry.returncode, 0)

    def test_blank_template_matches_native_initializer(self) -> None:
        """Keep the documented starter tied to actual pinned generator output."""
        module = ast.parse((UPSTREAM / "openai/scripts/init_skill.py").read_text())
        template = next(
            ast.literal_eval(n.value)
            for n in module.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "SKILL_TEMPLATE" for t in n.targets)
        )
        expected = template.replace("{skill_name}", "{{skill_name}}").replace(
            "{skill_title}", "{{display_name}}"
        )
        self.assertEqual(
            (ROOT.parent / "standards/authoring/templates/SKILL.md.template").read_text(), expected
        )

    def test_pairing_fresh_context_and_credential_cleanup(self) -> None:
        """Preserve planned pairs, alternating order, isolated configuration, and hidden grading."""
        plan = self.run_fixture(2)
        self.assertEqual(len(plan["runs"]), 4)
        self.assertIn("/with_skill/", plan["runs"][0])
        self.assertIn("/without_skill/", plan["runs"][2])
        for relative in plan["runs"]:
            root = self.output / relative
            self.assertFalse((root / "client/auth.json").exists())
            self.assertEqual(json.loads((root / "status.json").read_text())["total_tokens"], 5)
            self.assertIn("[agents]\nenabled = false", (root / "client/config.toml").read_text())

    def test_preflight_failure_retains_every_attempt_without_credentials_or_model(self) -> None:
        """Refuse unrestricted fallback and keep setup failures visible."""
        with (
            patch.object(native, "preflight", side_effect=ValueError("fixture-denied")),
            patch.object(native, "execute") as execute,
        ):
            plan = workflow.run(
                self.evals,
                self.skill,
                self.output,
                Path(sys.executable),
                self.auth,
                "fixture-model",
                "medium",
                1,
                2,
            )
        execute.assert_not_called()
        for relative in plan["runs"]:
            self.assertEqual(
                json.loads((self.output / relative / "status.json").read_text())["status"],
                "setup_error",
            )
            self.assertFalse((self.output / relative / "client/auth.json").exists())
        with self.assertRaises(ValueError):
            workflow.report(self.output)

    def test_report_uses_real_upstream_aggregation_and_static_viewer(self) -> None:
        """Produce compatible reports with correct direction, repeat count, and observed metrics."""
        plan = self.run_fixture()
        self.grade_fixture(plan)
        result = workflow.report(self.output)
        self.assertEqual(result["metadata"]["runs_per_configuration"], 1)
        self.assertEqual(result["run_summary"]["delta"]["pass_rate"], "+1.00")
        self.assertEqual(result["run_summary"]["with_skill"]["tokens"]["mean"], 5)
        self.assertEqual(result["run_summary"]["with_skill"]["time_seconds"]["mean"], 0.25)
        self.assertIn("<html", (self.output / "review.html").read_text().lower())

    def test_report_rejects_one_arm_and_unplanned_runs(self) -> None:
        """Require the complete declared product of cases, arms, and repetitions."""
        plan = self.run_fixture()
        self.grade_fixture(plan)
        changed = {**plan, "runs": plan["runs"][:1]}
        workflow.write_json(self.output / "plan.json", changed)
        with self.assertRaises(ValueError):
            workflow.report(self.output)
        workflow.write_json(self.output / "plan.json", plan)
        extra = self.output / "eval-1/with_skill/run-2"
        extra.mkdir()
        with self.assertRaises(ValueError):
            workflow.report(self.output)
        extra.rmdir()
        (self.output / "runs").mkdir()
        with self.assertRaises(ValueError):
            workflow.report(self.output)

    def test_runtime_executable_mode_is_preserved_and_recorded(self) -> None:
        """Allow directly invoked runtime helpers in the actor's read-only skill home."""
        script = self.skill / "scripts/helper.sh"
        script.parent.mkdir()
        script.write_text("#!/bin/sh\nprintf fixture\n")
        script.chmod(0o755)
        plan = self.run_fixture()
        staged = (
            self.output
            / "eval-1/with_skill/run-1/home/.agents/skills/fixture-skill/scripts/helper.sh"
        )
        self.assertEqual(staged.stat().st_mode & 0o777, 0o755)
        self.assertEqual(plan["skill_modes"]["scripts/helper.sh"], 0o755)
        self.assertTrue((self.output / plan["runs"][0] / "workspace/.git").is_dir())

    def test_static_view_includes_nested_deliverables_without_flat_name_collision(self) -> None:
        """Show nested artifacts and preserve ambiguous-looking original filenames."""
        plan = self.run_fixture()
        self.grade_fixture(plan)
        outputs = self.output / plan["runs"][0] / "outputs"
        (outputs / "nested").mkdir()
        (outputs / "nested/report.txt").write_text("nested-deliverable")
        (outputs / "nested%2Freport.txt").write_text("literal-percent-name")
        workflow.report(self.output)
        html = (self.output / "review.html").read_text()
        for expected in (
            "nested/report.txt",
            "nested%2Freport.txt",
            "nested-deliverable",
            "literal-percent-name",
        ):
            self.assertIn(expected, html)
        self.assertTrue((outputs / "nested/report.txt").exists())

    def test_viewer_supports_long_unicode_paths_and_escapes_script_terminators(self) -> None:
        """Keep valid output names and untrusted text intact without creating executable HTML."""
        plan = self.run_fixture()
        self.grade_fixture(plan)
        outputs = self.output / plan["runs"][0] / "outputs"
        name = "é" * 60 + ".txt"
        (outputs / name).write_text("long-deliverable </script><script>alert('fixture')</script>")
        relative = "/".join(["directory" * 4] * 10) + "/report.txt"
        nested = outputs / relative
        nested.parent.mkdir(parents=True)
        nested.write_text("deep-deliverable")
        workflow.report(self.output)
        html = (self.output / "review.html").read_text()
        self.assertIn(json.dumps(name), html)
        self.assertIn(json.dumps(relative), html)
        self.assertIn("long-deliverable", html)
        self.assertIn("deep-deliverable", html)
        self.assertNotIn("</script><script>alert", html)

    def test_missing_grades_or_unknown_tokens_never_become_a_score(self) -> None:
        """Prevent silent omission and upstream's token/output-character fallback."""
        plan = self.run_fixture()
        with self.assertRaises(OSError):
            workflow.report(self.output)
        self.grade_fixture(plan)
        workflow.write_json(
            self.output / plan["runs"][0] / "timing.json",
            {"total_tokens": None, "total_duration_seconds": 1},
        )
        with self.assertRaises(ValueError):
            workflow.report(self.output)
        self.assertFalse((self.output / "benchmark.json").exists())

    def test_blind_bundle_excludes_arm_mapping_and_expected_answers(self) -> None:
        """Supply only the task, assertions, neutral labels, and artifact copies to a reviewer."""
        self.run_fixture()
        destination = self.root / "blind"
        workflow.blind(self.output, destination)
        self.assertTrue((self.output / "blind-map.json").exists())
        self.assertFalse((destination / "blind-map.json").exists())
        text = "\n".join(v.decode() for v in workflow.files(destination).values())
        self.assertNotIn("private expected outcome", text)
        self.assertTrue((destination / "eval-1-run-1/A/result.txt").exists())
        self.assertTrue((destination / "eval-1-run-1/B/result.txt").exists())

    def test_cases_reject_aliases_and_conflicting_checks(self) -> None:
        """Validate input boundaries before creating an evaluation workspace."""
        for name in ("../fixture-auth.json", str(self.auth), ".codex/config.toml"):
            self.data["evals"][0]["files"] = [name]
            self.evals.write_text(json.dumps(self.data))
            with self.assertRaises(ValueError):
                workflow.cases(self.evals, self.skill)
        self.data["evals"][0]["files"] = []
        self.data["evals"][0]["assertions"] = ["Conflicting criterion."]
        self.evals.write_text(json.dumps(self.data))
        with self.assertRaises(ValueError):
            workflow.cases(self.evals, self.skill)

    def test_upstream_fingerprint_detects_modified_source(self) -> None:
        """Exercise source pinning in an isolated copy without editing vendored files."""
        package = self.root / "package"
        package.mkdir()
        target = self.root / "vendor.txt"
        target.write_bytes(b"original")
        digest = hashlib.sha1(b"blob 8\0original").hexdigest()
        workflow.write_json(
            package / "UPSTREAM.json", {"files": [{"path": "vendor.txt", "git_blob_sha": digest}]}
        )
        with patch.object(workflow, "ROOT", package):
            workflow.verify_upstream()
            target.write_text("changed")
            with self.assertRaises(ValueError):
                workflow.verify_upstream()

    def test_token_accounting_ignores_cached_subset_and_retains_unknown(self) -> None:
        """Count observed root usage without inventing data or double-counting cache hits."""
        trace = json.dumps(
            {
                "type": "turn.completed",
                "usage": {"input_tokens": 10, "cached_input_tokens": 8, "output_tokens": 2},
            }
        )
        self.assertEqual(native.tokens(trace + "\n" + trace), 24)
        self.assertIsNone(native.tokens("[]\nnot-json"))


if __name__ == "__main__":
    unittest.main()
