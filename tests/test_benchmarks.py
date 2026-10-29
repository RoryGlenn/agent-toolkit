"""Behavior checks for public benchmark controls, boundaries, and result accounting."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.__main__ import make_plan, prepare, read_plan, report, validate_controls, write_json
from benchmarks.cases import CASES, materialize
from benchmarks.oracles import Oracle, artifact_hashes, inspect_archive
from benchmarks.process import TrustedControlExecutor, bounded_process, sanitized_environment
from benchmarks.runtime import (
    NativeExecutor,
    config_text,
    digest,
    observe_trace,
    resource_manifest,
    stage_arm,
)


class BenchmarkControlsTests(unittest.TestCase):
    """Verify the benchmark detects wrong behavior rather than self-reported success."""

    def test_all_reference_and_wrong_controls(self) -> None:
        result = validate_controls()
        failed = [item for item in result["cases"] if not item["validated"]]
        self.assertFalse(failed, json.dumps(failed, indent=2))
        self.assertEqual(len(result["cases"]), 13)

    def test_contracts_and_fingerprints(self) -> None:
        self.assertEqual(len(CASES), 12)
        self.assertEqual(len({case.id for case in CASES}), 12)
        for case in CASES:
            with self.subTest(case=case.id):
                self.assertEqual(len(case.fingerprint), 64)
                self.assertIn("Python 3.11", case.task)
                self.assertFalse(case.manifest()["difficulty_calibrated"])

    def test_actor_staging_has_no_oracles_or_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "actor"
            materialize(workspace, CASES[0])
            self.assertEqual(
                set(artifact_hashes(workspace)),
                {"recordbatch.py", "build.py", "README.md", "TASK.md"},
            )
            self.assertNotIn("defect", (workspace / "recordbatch.py").read_text())

    def test_symlink_and_configuration_artifacts_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize(root / "actor", CASES[0])
            (root / "actor" / "alias").symlink_to(root / "outside")
            with self.assertRaisesRegex(ValueError, "symlink"):
                artifact_hashes(root / "actor")
            (root / "actor" / "alias").unlink()
            (root / "actor" / ".codex").mkdir()
            (root / "actor" / ".codex/config.toml").write_text("model='other'")
            with self.assertRaisesRegex(ValueError, "configuration"):
                artifact_hashes(root / "actor")

    def test_self_reported_success_does_not_score(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "actor"
            materialize(root, CASES[0])
            (root / "recordbatch.py").write_text('print("All tests passed")\n')
            grade = Oracle(root, CASES[0], TrustedControlExecutor()).run()
            self.assertEqual(grade.status, "failed")

    def test_archive_traversal_rejected(self) -> None:
        import zipfile

        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory).resolve() / "bad.pyz"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../outside", "bad")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                inspect_archive(archive)


class BenchmarkProfileTests(unittest.TestCase):
    """Check resources and controlled model settings without reading personal libraries."""

    def test_downloaded_resources_exclude_evaluations_and_instructions(self) -> None:
        files = resource_manifest("downloaded")
        self.assertTrue(any(name.endswith(".epub") for name in files))
        self.assertFalse(any("eval" in name or "SKILL.md" in name for name in files))
        self.assertFalse(any(name.startswith(".local") for name in files))

    def test_complete_profile_requires_explicit_fingerprinted_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit"):
            resource_manifest("reference-complete")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.epub"
            source.write_text("source")
            manifest = root / "manifest.json"
            write_json(
                manifest,
                {
                    "version": 1,
                    "files": [
                        {
                            "source": str(source),
                            "target": ".local/share/ddia-specialist/source.epub",
                            "sha256": "wrong",
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                resource_manifest("reference-complete", manifest)
            data = json.loads(manifest.read_text())
            data["files"][0]["sha256"] = digest(source)
            write_json(manifest, data)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                resource_manifest("reference-complete", manifest)
            data["files"][0]["target"] = ".local/share/ddia-specialist/evaluation/rubric.md"
            write_json(manifest, data)
            with self.assertRaisesRegex(ValueError, "evaluation"):
                resource_manifest("reference-complete", manifest)

    def test_controlled_roles_are_real_copies_with_equal_model_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home, client = root / "home", root / "client"
            home.mkdir()
            client.mkdir()
            metadata = stage_arm(home, client, "toolkit", "downloaded", "same-model", "medium")
            self.assertTrue(metadata["toolkit_files"])
            for path in (client / "agents").glob("*.toml"):
                self.assertFalse(path.is_symlink())
                data = tomllib.loads(path.read_text())
                self.assertEqual(data["model"], "same-model")
                self.assertEqual(data["model_reasoning_effort"], "medium")
                self.assertNotIn("sandbox_mode", data)
            self.assertFalse(list(home.rglob("evals")))

    def test_sources_are_matched_without_skill_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hashes = []
            for arm in ("baseline", "source-matched", "toolkit"):
                home, client = root / arm, root / (arm + "-client")
                home.mkdir()
                client.mkdir()
                metadata = stage_arm(home, client, arm, "downloaded", "same", "high")
                hashes.append(metadata["source_fingerprint"])
                if arm != "toolkit":
                    self.assertFalse(list(home.rglob("SKILL.md")))
                    self.assertFalse((client / "agents").exists())
            self.assertEqual(len(set(hashes)), 1)

    def test_git_is_canonical_and_host_configuration_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            home, client = root / "home", root / "client"
            home.mkdir()
            client.mkdir()
            metadata = stage_arm(home, client, "baseline", "downloaded", "same", "high")
            git = metadata["git_runtime"]
            self.assertEqual((home / "bin/git").resolve(), Path(git["executable"]))
            self.assertNotEqual(git["executable"], "/usr/bin/xcrun")
            config = tomllib.loads(
                config_text(root / "workspace", home, client, root / "tmp", "same", "high")
            )
            permissions = config["permissions"]["benchmark"]["filesystem"]
            self.assertEqual(permissions[git["executable"]], "read")
            self.assertEqual(permissions[git["exec_path"]], "read")
            self.assertNotIn("/Library/Developer/CommandLineTools", permissions)
            self.assertNotIn(str(Path.home()), permissions)
            environment = config["shell_environment_policy"]["set"]
            self.assertEqual(environment["GIT_CEILING_DIRECTORIES"], str(root))
            self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertEqual(environment["GIT_CONFIG_GLOBAL"], "/dev/null")
            self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_permission_config_denies_default_access_and_parent_config_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = tomllib.loads(
                config_text(
                    root / "workspace",
                    root / "home",
                    root / "client",
                    root / "tmp",
                    "same",
                    "high",
                    1000,
                )
            )
            self.assertNotIn("sandbox_mode", data)
            self.assertEqual(data["default_permissions"], "benchmark")
            permissions = data["permissions"]["benchmark"]
            self.assertEqual(permissions["filesystem"][":root"], "deny")
            self.assertEqual(permissions["filesystem"][str((root / "home").resolve())], "read")
            self.assertNotIn(str(root / "client"), permissions["filesystem"])
            self.assertFalse(permissions["network"]["enabled"])
            self.assertFalse(data["skills"]["bundled"]["enabled"])
            self.assertEqual(data["shell_environment_policy"]["inherit"], "none")
            self.assertEqual(data["features"]["rollout_budget"]["limit_tokens"], 1000)


class BenchmarkAccountingTests(unittest.TestCase):
    """Keep attempt failures and incompatible comparisons visible."""

    def result(self, arm: str, status: str, run_id: str, **extra: object) -> dict[str, object]:
        return {
            "run_id": run_id,
            "plan_id": "paired",
            "case_id": "design-easy",
            "phase": 1,
            "arm": arm,
            "status": status,
            "attempt": 1,
            "model": "same",
            **extra,
        }

    def test_report_retains_failed_and_unknown_attempts(self) -> None:
        results = [
            self.result("baseline", "failed", "a", grade={"failures": ["wrong"]}),
            self.result("source-matched", "timed_out", "b"),
            self.result(
                "toolkit",
                "needs_review",
                "c",
                grade={
                    "failures": [],
                    "needs_review": ["reader study"],
                    "objective_complete": True,
                    "checks": ["objective"],
                    "commands": [{"argv": ["tested"], "returncode": 0}],
                    "case_id": "design-easy",
                    "phase": 1,
                    "status": "needs_review",
                },
            ),
        ]
        summary = report(results)
        self.assertEqual(summary["attempts"], 3)
        self.assertEqual(summary["distinct_tasks"], 1)
        pair = summary["groups"][0]["pairs"][0]
        self.assertEqual(pair["arms"], {"baseline": False, "source-matched": None, "toolkit": True})
        self.assertFalse(pair["all_objectively_evaluable"])
        self.assertTrue(all(item["cost"] is None for item in summary["groups"][0]["attempts"]))

    def test_report_separates_models_and_rejects_duplicates(self) -> None:
        first = self.result("baseline", "failed", "a")
        changed = self.result("toolkit", "failed", "b", model="different")
        self.assertEqual(len(report([first, changed])["groups"]), 2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            report([first, first])

    def test_trace_discovery_is_not_usage_and_unknown_is_not_zero(self) -> None:
        output = observe_trace(json.dumps({"type": "agent_message", "text": "I used ddia_agent"}))
        self.assertEqual(output["role_dispatch_observed"], [])
        self.assertEqual(output["source_access_observed"], [])
        self.assertIsNone(output["aggregate_tree_tokens"])
        self.assertIsNone(output["cost"])

    def test_plan_bounds_staleness_and_reproducible_pair_order(self) -> None:
        args = (
            ["design-easy"],
            ["baseline", "source-matched", "toolkit"],
            "model",
            "high",
            "downloaded",
            60,
            1,
            None,
            "controlled",
            None,
        )
        plan = make_plan(*args)
        self.assertEqual(plan["entries"], make_plan(*args)["entries"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            plan["entries"][0]["case_fingerprint"] = "stale"
            write_json(path, plan)
            with self.assertRaisesRegex(ValueError, "changed"):
                read_plan(path)
        with self.assertRaisesRegex(ValueError, "attempts"):
            make_plan(*args[:6], 5, *args[7:])

    def test_model_advertised_effort_is_preserved_without_a_closed_enum(self) -> None:
        for effort in ("ultra", "future-model-effort"):
            with self.subTest(effort=effort), tempfile.TemporaryDirectory() as directory:
                plan = make_plan(
                    ["design-easy"],
                    ["toolkit"],
                    "gpt-6-astra",
                    effort,
                    "downloaded",
                    60,
                    1,
                    None,
                    "controlled",
                    None,
                )
                self.assertEqual(plan["effort"], effort)
                root = Path(directory).resolve() / "attempt"
                result = prepare(plan, plan["entries"][0], root)
                self.assertEqual(result["effort"], effort)
                config = tomllib.loads((root / "client-home/config.toml").read_text())
                self.assertEqual(config["model_reasoning_effort"], effort)
                self.assertEqual(config["agents"]["default_subagent_reasoning_effort"], effort)
                for role in (root / "client-home/agents").glob("*.toml"):
                    self.assertEqual(
                        tomllib.loads(role.read_text())["model_reasoning_effort"], effort
                    )
        for effort in ("", "   "):
            with self.subTest(effort=effort), self.assertRaisesRegex(ValueError, "nonempty"):
                make_plan(
                    ["design-easy"],
                    ["baseline"],
                    "gpt-6-astra",
                    effort,
                    "downloaded",
                    60,
                    1,
                    None,
                    "controlled",
                    None,
                )

    def test_prepare_never_overwrites_prior_attempt(self) -> None:
        plan = make_plan(
            ["design-easy"],
            ["baseline"],
            "model",
            "high",
            "downloaded",
            60,
            1,
            None,
            "controlled",
            None,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "attempt"
            prepare(plan, plan["entries"][0], root)
            with self.assertRaises(FileExistsError):
                prepare(plan, plan["entries"][0], root)


class BenchmarkProcessTests(unittest.TestCase):
    """Verify deadlines, cleanup, output bounds, and fail-closed sandbox behavior."""

    def test_timeout_and_output_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = sanitized_environment(root, root)
            result = bounded_process(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                root,
                environment,
                timeout=0.15,
            )
            self.assertTrue(result.timed_out)
            self.assertLess(result.elapsed_seconds, 3)
            result = bounded_process(
                [sys.executable, "-c", "print('x'*1000000)"], root, environment, max_output=1000
            )
            self.assertLessEqual(len(result.stdout), 1000)

    @unittest.skipUnless(os.name == "posix", "POSIX process-group behavior")
    def test_timeout_cleans_background_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = (
                "import subprocess,time,pathlib; "
                f"p=subprocess.Popen([{sys.executable!r},'-c','import time; time.sleep(30)']); "
                "pathlib.Path('pid').write_text(str(p.pid)); time.sleep(30)"
            )
            result = bounded_process(
                [sys.executable, "-c", script], root, sanitized_environment(root, root), timeout=0.3
            )
            self.assertTrue(result.timed_out)
            pid = int((root / "pid").read_text())
            # A killed child may briefly remain an OS zombie; it must not be running.
            probe = bounded_process(
                ["/bin/ps", "-p", str(pid), "-o", "stat="], root, sanitized_environment(root, root)
            )
            self.assertTrue(not probe.stdout.strip() or probe.stdout.strip().startswith("Z"))

    def test_executor_refuses_unverified_or_unsupported_native_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executor = NativeExecutor(Path("/missing/codex"), root, root, root, root)
            with self.assertRaisesRegex(ValueError, "not passed"):
                executor.execute(["true"], root)
            with patch("benchmarks.runtime.platform.system", return_value="Windows"):
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    executor.preflight([root / "outside"])


if __name__ == "__main__":
    unittest.main()
