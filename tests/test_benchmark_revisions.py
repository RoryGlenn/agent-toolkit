"""Regressions for independent review findings, including real native alias containment."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack, closing
from pathlib import Path
from unittest.mock import patch

from benchmarks.__main__ import (
    attempt_directory,
    campaign_results,
    copy_project,
    create_executor,
    initialize_campaign,
    make_plan,
    preflight,
    prepare,
    report,
    run_attempt,
    seal_result,
    write_json,
)
from benchmarks.cases import ROOT, example, get_case, materialize
from benchmarks.files import copy_snapshot, hashes, read_regular, snapshot
from benchmarks.oracles import Oracle, identical_retry
from benchmarks.process import Execution, TrustedControlExecutor
from benchmarks.runtime import (
    ARMS,
    HARNESS_ROOT,
    REPOSITORY,
    NativeExecutor,
    config_text,
    resolve_codex,
    skill_names,
    stage_runtime,
)


class OracleRegressionTests(unittest.TestCase):
    """Reject specific false-positive controls found by independent review."""

    def test_no_op_delete_fails_persistent_and_capacity_controls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("design-easy")
            materialize(root, case, "reference")
            source = root / "recordbatch.py"
            source.write_text(
                source.read_text().replace(
                    'connection.execute("DELETE FROM jobs WHERE tenant=? AND id=?", '
                    "(tenant, job_id))",
                    "return  # deliberately wrong no-op",
                )
            )
            grade = Oracle(root, case, TrustedControlExecutor()).run()
            self.assertEqual(grade.status, "failed")
            self.assertIn("deleted job is persistently absent", grade.failures)
            self.assertIn("new admission after deletion", grade.failures)

    def test_all_forbidden_quickstart_does_not_establish_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("docs-easy")
            materialize(root, case, "reference")
            steps = [
                example(
                    {
                        "op": operation,
                        "tenant": "a",
                        "principal": "b",
                        "key": "never",
                        "payload": {},
                    },
                    {"ok": False, "error": "forbidden"},
                )
                for operation in ("init", "submit", "status")
            ]
            (root / "README.md").write_text(
                "```recordbatch\n" + json.dumps({"steps": steps}) + "\n```\n"
            )
            grade = Oracle(root, case, TrustedControlExecutor()).run()
            self.assertEqual(grade.status, "failed")
            self.assertIn("documented successful queued acceptance", grade.failures)

    def test_malformed_status_results_fail_without_escaping_grader(self) -> None:
        for replacement in ("[]", "None", "{}"):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve() / "project"
                case = get_case("integrated-easy")
                materialize(root, case, "reference")
                source = root / "recordbatch.py"
                source.write_text(
                    source.read_text().replace(
                        "return [self.job(row) for row in rows]", f"return {replacement}"
                    )
                )
                grade = Oracle(root, case, TrustedControlExecutor()).run()
                self.assertEqual(grade.status, "failed")
                self.assertFalse(grade.objective_complete)

    def test_unexpected_controller_error_is_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("design-easy")
            materialize(root, case, "reference")
            with patch.object(Oracle, "execute", side_effect=RuntimeError("harness broke")):
                grade = Oracle(root, case, TrustedControlExecutor()).run()
            self.assertEqual(grade.status, "harness_error")
            self.assertIn("harness broke", grade.harness_error or "")

    def test_recursive_view_query_is_bounded_outside_grader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("ddia-medium")
            materialize(root, case, "reference")
            with closing(sqlite3.connect(root / "state.sqlite")) as connection:
                connection.execute(
                    "CREATE VIEW jobs AS WITH RECURSIVE endless(x) AS "
                    "(SELECT 1 UNION ALL SELECT x+1 FROM endless) "
                    "SELECT x AS id, 'a' AS tenant FROM endless"
                )
                connection.commit()
            oracle = Oracle(root, case, TrustedControlExecutor())
            started = time.monotonic()
            with self.assertRaisesRegex(ValueError, "bounded database inspection"):
                oracle.sql("SELECT count(*) FROM jobs WHERE tenant='a'")
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual(oracle.grade.commands[-1]["returncode"], 2)
            self.assertIn("interrupted", oracle.grade.commands[-1]["stderr"])

    def test_wal_reference_preserves_deletion_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("design-easy")
            materialize(root, case, "reference")
            source = root / "recordbatch.py"
            source.write_text(
                source.read_text().replace(
                    "        connection.row_factory = sqlite3.Row",
                    '        connection.execute("PRAGMA journal_mode=WAL")\n'
                    "        connection.row_factory = sqlite3.Row",
                )
            )
            grade = Oracle(root, case, TrustedControlExecutor()).run()
            self.assertEqual(grade.status, "passed", grade.failures)

    def test_sql_snapshot_includes_committed_wal_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "project"
            case = get_case("design-easy")
            materialize(root, case, "reference")
            # Keep a connection open so committed schema/data remain in WAL, not main.
            with closing(sqlite3.connect(root / "state.sqlite")) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA wal_autocheckpoint=0")
                connection.execute("CREATE TABLE wal_probe(value INTEGER)")
                connection.execute("INSERT INTO wal_probe VALUES(73)")
                connection.commit()
                self.assertGreater((root / "state.sqlite-wal").stat().st_size, 0)
                oracle = Oracle(root, case, TrustedControlExecutor())
                self.assertEqual(oracle.sql("SELECT value FROM wal_probe"), [(73,)])

    def test_docs_retry_requires_identical_request_not_two_successes(self) -> None:
        for difference in ("tenant", "key", "payload", "database"):
            with self.subTest(difference=difference), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve() / "project"
                case = get_case("docs-medium")
                materialize(root, case, "reference")
                text = (root / "README.md").read_text()
                block = re.search(r"```recordbatch\n(.*?)\n```", text, re.S)
                assert block is not None
                procedure = json.loads(block[1])
                steps = procedure["steps"]
                retry, conflict = steps[3], steps[4]
                request = json.loads(retry["argv"][-1])
                if difference == "tenant":
                    request["tenant"] = "other"
                    retry["expect"]["job"]["id"] = 2
                elif difference == "database":
                    retry["argv"][3] = "other.sqlite"
                elif difference == "key":
                    steps.insert(
                        3,
                        example(
                            {"op": "complete", "id": 1}, {"ok": True, "job": {"state": "completed"}}
                        ),
                    )
                    request["key"] = "different"
                    retry["expect"]["job"]["id"] = 2
                    steps[-1]["expect"]["jobs"].append(
                        {
                            "id": 2,
                            "tenant": "demo",
                            "key": "different",
                            "payload": {"value": 7},
                            "state": "queued",
                        }
                    )
                else:
                    steps.insert(3, example({"op": "delete", "id": 1}, {"ok": True}))
                    request["payload"] = {"value": 8}
                    conflict_request = json.loads(conflict["argv"][-1])
                    conflict_request["payload"] = {"value": 9}
                    conflict["argv"][-1] = json.dumps(conflict_request)
                    steps[-1]["expect"]["jobs"][0]["payload"] = {"value": 8}
                retry["argv"][-1] = json.dumps(request)
                (root / "README.md").write_text(
                    text[: block.start(1)] + json.dumps(procedure) + text[block.end(1) :]
                )
                grade = Oracle(root, case, TrustedControlExecutor()).run()
                self.assertEqual(grade.failures, ["documented retry exercised"])

    def test_retry_payload_canonicalization_and_logical_job_identity(self) -> None:
        first = {
            "database": "/same/db.sqlite",
            "request": {"op": "submit", "key": "x", "payload": {"a": 1, "b": 2}},
            "response": {
                "ok": True,
                "job": {
                    "id": 1,
                    "tenant": "demo",
                    "key": "x",
                    "payload": {"a": 1, "b": 2},
                    "state": "queued",
                },
            },
        }
        repeat = json.loads(json.dumps(first))
        repeat["request"]["payload"] = {"b": 2, "a": 1}
        repeat["response"]["job"]["state"] = "completed"
        self.assertTrue(identical_retry([first, repeat]))
        repeat["response"]["job"]["id"] = 2
        self.assertFalse(identical_retry([first, repeat]))

    def test_parent_and_final_alias_reads_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "protected").write_text("marker")
            (root / "alias").symlink_to(root, target_is_directory=True)
            (root / "linked").hardlink_to(root / "protected")
            for target in (root / "alias/protected", root / "linked"):
                with self.subTest(target=target), self.assertRaises((OSError, ValueError)):
                    read_regular(target)

    @unittest.skipUnless(shutil.which("codex"), "native Codex CLI not installed")
    def test_native_global_temp_denial_preserves_explicit_narrow_grants(self) -> None:
        with ExitStack() as stack:
            root = Path(stack.enter_context(tempfile.TemporaryDirectory())).resolve()
            scratch = [
                Path(stack.enter_context(tempfile.TemporaryDirectory(dir=parent))).resolve()
                for parent in ("/tmp", "/var/tmp")
            ]
            home, client = root / "home", root / "client"
            workspace, temporary = scratch[0] / "workspace", scratch[1] / "private"
            readonly = [directory / "readonly" for directory in scratch]
            for path in (home, client, workspace, temporary, *readonly):
                path.mkdir()
            stage_runtime(home)
            for path in readonly:
                (path / "role.toml").write_text("known-readonly")
            forbidden = root / "protected"
            forbidden.write_text("known-protected")
            targets = [directory / "outside" for directory in scratch]
            for path in targets:
                path.write_text("known-outside")
            # Exercise both lexical macOS aliases and their canonical /private paths.
            aliases = [
                Path(parent) / directory.name / "outside"
                for parent, directory in zip(("/tmp", "/var/tmp"), scratch, strict=True)
            ]
            denied = [str(path) for pair in zip(targets, aliases, strict=True) for path in pair]
            created = [str(directory / "new-sibling") for directory in scratch]
            (client / "config.toml").write_text(
                config_text(
                    workspace, home, client, temporary, "unused", "low", readonly_extra=readonly
                )
            )
            executor = NativeExecutor(resolve_codex(), client, home, temporary, workspace)
            self.assertTrue(all(executor.preflight([forbidden])[0]["checks"].values()))
            script = f"""import json, pathlib, tempfile
out={{}}
for index,name in enumerate({denied!r}):
    path=pathlib.Path(name)
    for operation in ('read', 'write'):
        try:
            path.read_bytes() if operation=='read' else path.write_text('changed-by-actor')
        except OSError as error:
            out[f'{{operation}}_{{index}}']=error.errno in (1,2,13,30)
        else:
            out[f'{{operation}}_{{index}}']=False
for index,name in enumerate({created!r}):
    try:
        pathlib.Path(name).write_text('new-outside')
    except OSError as error:
        out['create_'+str(index)]=error.errno in (1,2,13,30)
    else:
        out['create_'+str(index)]=False
for index,name in enumerate({[str(path / "role.toml") for path in readonly]!r}):
    out['readonly_'+str(index)]=pathlib.Path(name).read_text()=='known-readonly'
with tempfile.NamedTemporaryFile(mode='w+', dir={str(temporary)!r}) as stream:
    stream.write('private'); stream.seek(0)
    out['private_temp']=stream.read()=='private'
path=pathlib.Path({str(workspace / "created")!r})
path.write_text('workspace')
out['workspace']=path.read_text()=='workspace'
print(json.dumps(out))
"""
            result = executor.execute(
                [str(Path(sys.executable).resolve()), "-I", "-B", "-c", script], workspace
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            checks = json.loads(result.stdout)
            self.assertTrue(all(checks.values()), checks)
            self.assertTrue(all(path.read_text() == "known-outside" for path in targets))
            self.assertTrue(all(not Path(path).exists() for path in created))
            self.assertTrue(
                all((path / "role.toml").read_text() == "known-readonly" for path in readonly)
            )

    @unittest.skipUnless(shutil.which("codex"), "native Codex CLI not installed")
    def test_native_git_inside_repository_stops_parent_discovery(self) -> None:
        runs = REPOSITORY / ".benchmark-runs"
        runs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="git-preflight-test-", dir=runs) as directory:
            root = Path(directory).resolve() / "attempt"
            plan = make_plan(
                ["design-easy"],
                ["baseline"],
                "unused",
                "ultra",
                "downloaded",
                60,
                1,
                None,
                "controlled",
                None,
            )
            prepare(plan, plan["entries"][0], root)
            executor = create_executor(root, resolve_codex())
            checks = preflight(executor, root)[0]["checks"]
            self.assertTrue(checks["allowed_git_version"])
            self.assertTrue(checks["allowed_git_diff"])
            self.assertTrue(checks["isolated_git_config"])
            self.assertTrue(all(checks.values()))

    @unittest.skipUnless(
        shutil.which("codex"), "native Codex CLI not installed; CI uses controls only"
    )
    def test_native_grader_cannot_overwrite_protected_alias_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "run"
            plan = make_plan(
                ["integrated-medium"],
                ["baseline"],
                "unused",
                "high",
                "downloaded",
                60,
                1,
                None,
                "controlled",
                None,
            )
            prepare(plan, plan["entries"][0], root)
            protected = root / "protected.txt"
            protected.write_text("controller marker")
            project = root / "workspace"
            (project / "recordbatch.py").write_bytes(
                (ROOT / "recordbatch/recordbatch.py").read_bytes()
            )
            build = project / "build.py"
            build.write_text(
                build.read_text() + "\nconsumer = Path(__file__).parent / 'consumer'\n"
                "consumer.mkdir()\n"
                + f"(consumer/'recordbatch.pyz').symlink_to({str(protected)!r})\n"
                + f"(consumer/'upgrade.sqlite').symlink_to({str(protected)!r})\n"
            )
            executor = create_executor(root, resolve_codex())
            checks = preflight(executor, root)[0]["checks"]
            self.assertTrue(all(checks.values()))
            self.assertTrue(checks["allowed_git_version"])
            self.assertTrue(checks["allowed_git_diff"])
            self.assertTrue(checks["isolated_git_config"])
            grade = Oracle(project, get_case("integrated-medium"), executor).run()
            self.assertEqual(protected.read_text(), "controller marker")
            self.assertIn("archive-only fresh consumer", grade.checks)
            self.assertEqual(grade.status, "failed")
            self.assertTrue(any("symlink" in failure for failure in grade.failures))


class CampaignRegressionTests(unittest.TestCase):
    """Use persisted plans/artifacts/evidence to exercise replay and tamper boundaries."""

    def plan(self, arms: list[str] | None = None) -> dict[str, object]:
        return make_plan(
            ["design-easy"],
            arms or list(ARMS),
            "unused",
            "high",
            "downloaded",
            60,
            1,
            None,
            "controlled",
            None,
        )

    def completed_first(self, root: Path) -> Path:
        plan = self.plan()
        initialize_campaign(root, plan)
        entry = plan["entries"][0]
        attempt = root / attempt_directory(0, entry)
        result = prepare(plan, entry, attempt)
        (attempt / "workspace/recordbatch.py").write_bytes(
            (ROOT / "recordbatch/recordbatch.py").read_bytes()
        )
        frozen = snapshot(attempt / "workspace")
        copy_snapshot(frozen, attempt / "artifact")
        result["artifact_hashes"] = hashes(frozen)
        copy_project(attempt / "artifact", attempt / "grading")
        grade = Oracle(attempt / "grading", get_case("design-easy"), TrustedControlExecutor()).run()
        result.update(grade=grade.to_dict(), status=grade.status)
        seal_result(attempt, result)
        return attempt

    def test_missing_results_remain_in_saved_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "campaign"
            self.completed_first(root)
            results = campaign_results(root)
            self.assertEqual(len(results), 3)
            self.assertEqual(sum(result["status"] == "not_started" for result in results), 2)
            summary = report(results)
            self.assertEqual(summary["attempts"], 3)
            self.assertFalse(summary["groups"][0]["pairs"][0]["complete"])
            self.assertFalse(summary["groups"][0]["pairs"][0]["all_objectively_evaluable"])

    def test_pair_completion_requires_terminal_outcomes_for_planned_arms(self) -> None:
        plan = self.plan()
        rows = [
            {**plan, **entry, "run_id": str(index), "status": "failed"}
            for index, entry in enumerate(plan["entries"])
        ]
        self.assertTrue(report(rows)["groups"][0]["pairs"][0]["complete"])
        for status in ("not_started", "interrupted_setup", "running", "prepared", "completed"):
            rows[1]["status"] = status
            self.assertFalse(report(rows)["groups"][0]["pairs"][0]["complete"])
        only = rows[0]
        only["planned_arms"] = [only["arm"]]
        pair = report([only])["groups"][0]["pairs"][0]
        self.assertTrue(pair["complete"])
        self.assertFalse(pair["three_arm_comparison"])

    def test_artifact_and_grade_tampering_are_rejected_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "campaign"
            attempt = self.completed_first(root)
            result_path = attempt / "result.json"
            original = result_path.read_bytes()
            result = json.loads(original)
            result["grade"]["checks"] = []
            write_json(result_path, result)
            with self.assertRaisesRegex(ValueError, "changed"):
                campaign_results(root)
            result_path.write_bytes(original)
            (attempt / "artifact/recordbatch.py").write_text("raise RuntimeError('changed')\n")
            with self.assertRaisesRegex(ValueError, "artifact changed"):
                campaign_results(root)

    def test_sealed_but_incomplete_grade_cannot_claim_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "campaign"
            attempt = self.completed_first(root)
            result = json.loads((attempt / "result.json").read_text())
            result["grade"]["checks"] = []
            seal_result(attempt, result)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                campaign_results(root)

    def test_toolkit_change_since_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repository = root / "repo"
            for name in ("skills", "agents", "books"):
                shutil.copytree(REPOSITORY / name, repository / name)
            with patch("benchmarks.runtime.REPOSITORY", repository):
                plan = self.plan(["toolkit"])
                skill = repository / "skills/ddia-skill/SKILL.md"
                skill.write_text(skill.read_text() + "\nChanged after planning.\n")
                with self.assertRaisesRegex(ValueError, "toolkit changed"):
                    prepare(plan, plan["entries"][0], root / "attempt")

    def test_changed_runtime_after_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            harness = root / "harness"
            shutil.copytree(HARNESS_ROOT, harness, ignore=shutil.ignore_patterns("__pycache__"))
            with patch("benchmarks.runtime.HARNESS_ROOT", harness):
                plan = self.plan(["baseline"])
                result = prepare(plan, plan["entries"][0], root / "before")
                self.assertEqual(result["harness_fingerprint"], plan["harness_fingerprint"])
                runtime = harness / "runtime.py"
                runtime.write_text(runtime.read_text() + "\n# Runtime changed after planning.\n")
                with self.assertRaisesRegex(ValueError, "harness changed"):
                    prepare(plan, plan["entries"][0], root / "after")

    def test_report_separates_harness_revisions_and_unrecorded_legacy_plans(self) -> None:
        plan = self.plan()
        rows = [
            {**plan, **entry, "run_id": str(index), "status": "failed"}
            for index, entry in enumerate(plan["entries"][:2])
        ]
        rows[1]["harness_fingerprint"] = "different-runtime"
        self.assertEqual(len(report(rows)["groups"]), 2)
        for index, row in enumerate(rows):
            row.pop("harness_fingerprint")
            row["plan_id"] = f"legacy-plan-{index}"
        groups = report(rows)["groups"]
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(group["comparison"]["harness_fingerprint"] is None for group in groups))

    def test_parent_and_parent_receipt_cannot_be_rebound_after_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            materialize(root / "artifact", get_case("design-hard"), "reference")
            parent = root / "result.json"
            data = {
                "case_id": "design-hard",
                "phase": 1,
                "artifact_hashes": hashes(snapshot(root / "artifact")),
            }
            write_json(parent, data)
            plan = make_plan(
                ["design-hard"],
                ["baseline"],
                "unused",
                "high",
                "downloaded",
                60,
                1,
                None,
                "controlled",
                None,
                2,
                parent,
            )
            (root / "artifact/README.md").write_text("changed after plan")
            data["artifact_hashes"] = hashes(snapshot(root / "artifact"))
            write_json(parent, data)
            with self.assertRaisesRegex(ValueError, "parent artifact changed"):
                prepare(plan, plan["entries"][0], root / "sequel")

    def test_auth_precedes_catalog_and_harness_failure_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            auth = root / "selected-auth.json"
            auth.write_text("not-real-test-auth")
            plan = self.plan(["baseline"])
            entry = plan["entries"][0]
            attempt = root / "attempt"

            def catalog(executor: object, location: Path) -> dict[str, object]:
                self.assertEqual(
                    (location / "client-home/auth.json").read_text(), "not-real-test-auth"
                )
                return {"tested_order": True}

            with (
                patch("benchmarks.__main__.preflight", return_value=[]),
                patch("benchmarks.__main__.verify_prompt_surface", side_effect=catalog),
                patch(
                    "benchmarks.__main__.bounded_process",
                    return_value=Execution(["fake"], 0, "", "", 0),
                ),
                patch.object(Oracle, "run", side_effect=RuntimeError("unexpected grader error")),
            ):
                result = run_attempt(plan, entry, attempt, Path("/bin/true"), auth)
            self.assertEqual(result["status"], "harness_error")
            self.assertFalse((attempt / "client-home/auth.json").exists())
            self.assertTrue((attempt / "result.sha256").is_file())
            self.assertIn("unexpected grader error", result["error"])

    def test_all_nine_skills_are_staged(self) -> None:
        self.assertEqual(len(skill_names()), 9)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "attempt"
            plan = self.plan(["toolkit"])
            prepare(plan, plan["entries"][0], root)
            self.assertEqual(len(list((root / "actor-home/.agents/skills").glob("*/SKILL.md"))), 9)


if __name__ == "__main__":
    unittest.main()
