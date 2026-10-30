"""Production-delta transfer, strict readiness and actual Linux resource regression checks."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from benchmarks.files import hash_regular
from benchmarks.large_projects.__main__ import main as large_main
from benchmarks.large_projects.adapters import VS_REGRESSIONS, Command, commands
from benchmarks.large_projects.artifacts import (
    apply_delta,
    freeze_delta,
    scope_contract,
    tree_hashes,
)
from benchmarks.large_projects.candidate import (
    actor_environment,
    grade_record,
    load_context,
    validate_context,
)
from benchmarks.large_projects.deadline import supervise
from benchmarks.large_projects.grading import candidate_compile_failure
from benchmarks.large_projects.integration import (
    case_at,
    dependency_paths,
    evaluate,
    evaluator_command,
    unpack_trusted,
    verify_bundle,
)
from benchmarks.large_projects.native import validate_native
from benchmarks.large_projects.qualification import kernel_controls, watchdog_controls
from benchmarks.large_projects.resources import (
    IMAGE,
    Deadline,
    Limits,
    ResourceCell,
    checked_toolchains,
    docker,
    require,
)
from benchmarks.large_projects.runner import harness_hashes
from benchmarks.process import Execution, bounded_process
from benchmarks.runtime import stage_runtime


class PipelineDataTests(unittest.TestCase):
    """Archive data and incomplete checks cannot become authoritative passing evidence."""

    def test_actor_keeps_canonical_runtime_and_private_bison_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory).resolve()
            (stage / "actor-home").mkdir()
            stage_runtime(stage / "actor-home")
            tools = stage / "tools"
            (tools / "bin").mkdir(parents=True)
            (tools / "share/bison").mkdir(parents=True)
            env = actor_environment(stage, [tools])
            python = shutil.which("python", path=env["PATH"])
            self.assertIsNotNone(python)
            self.assertEqual(Path(python or "").resolve(), Path(sys.executable).resolve())
            self.assertEqual(env["BISON_PKGDATADIR"], str(tools / "share/bison"))
            self.assertEqual(env["GOPROXY"], "off")

    def test_explicit_preinstalled_browser_never_uses_a_download_cache(self) -> None:
        mode = {"mode": "preinstalled"}
        self.assertEqual(
            dependency_paths("vscode-snippet-selections", mode),
            ("workspace/node_modules", "workspace/build/node_modules"),
        )
        self.assertIn("cache/playwright", dependency_paths("vscode-snippet-selections", None))
        with self.assertRaises(ValueError):
            dependency_paths("otel-queue-cancellation", mode)

    def test_deferred_dependency_links_cannot_create_any_host_outside_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            archive = root / "links.tar"
            with tarfile.open(archive, "w") as output:
                for name, target in (
                    ("a", "."),
                    ("a/escape", ".."),
                    ("a/escape/leaked", "payload"),
                ):
                    member = tarfile.TarInfo("node_modules/" + name)
                    member.type = tarfile.SYMTYPE
                    member.linkname = target
                    output.addfile(member)
            with self.assertRaises(ValueError):
                unpack_trusted(archive, root / "destination", "node_modules")
            self.assertFalse((root / "leaked").is_symlink())
            self.assertFalse((root / "leaked").exists())

    def test_candidate_sees_scope_and_unsupported_helper_fails_before_execution(self) -> None:
        case = case_at("otel-queue-cancellation")
        self.assertIn("exporter/exporterhelper/internal/queue/*.go", scope_contract(case["id"]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            parent = root / "parent"
            parent.mkdir()
            helper = "outside_component.go"
            (parent / helper).write_text("old production")
            archive = root / "worker.tar"
            with tarfile.open(archive, "w") as output:
                data = b"new production"
                member = tarfile.TarInfo("workspace/" + helper)
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
            artifact = root / "artifact"
            frozen = freeze_delta(case["id"], archive, parent, artifact)
            self.assertEqual(frozen["unsupported_production_changes"], [helper])
            with patch(
                "benchmarks.large_projects.integration.export_parent",
                side_effect=lambda _c, _r, target: shutil.copytree(parent, target),
            ):
                outcome = evaluate(
                    case,
                    root / "curator",
                    root / "evaluation",
                    [],
                    Deadline(30),
                    str(uuid.uuid4()),
                    Limits(),
                    artifact=artifact,
                )
            grade = grade_record(case["id"], outcome)
            self.assertEqual(grade["status"], "failed")
            self.assertTrue(grade["failures"])
            self.assertFalse(grade["objective_complete"])
            self.assertEqual(grade["commands"], [])

    def test_prefetch_and_trusted_host_discovery_use_separate_paths(self) -> None:
        remote = Path("/container-only/workspace")
        dependencies = commands(
            "vscode-snippet-selections", remote, Path("/build"), "fixed", dependency_only=True
        )
        self.assertEqual(
            [c.name for c in dependencies],
            ["node-version", "npm-version", "dependencies-root", "dependencies-build", "browser"],
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory).resolve()
            tests = source / "src/vs/editor/contrib/snippet/test/browser"
            tests.mkdir(parents=True)
            titles = [*sorted(VS_REGRESSIONS), *(f"existing {n}" for n in range(79))]
            (tests / "snippetSession.test.ts").write_text(
                "\n".join(f"test({title!r}, () => {{}});" for title in titles)
                + "\ntest.skip('existing pending', () => {});\n"
            )
            (tests / "snippetController2.test.ts").write_text("")
            plan = commands(
                "vscode-snippet-selections",
                remote,
                Path("/build"),
                "fixed",
                discovery_source=source,
            )
            browser = plan[-1]
            self.assertEqual(len(browser.expected), 86)
            self.assertEqual(list(browser.expected.values()).count("skip"), 1)
            self.assertEqual(browser.cwd, remote)

    def test_frozen_delta_restores_authoritative_tests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            parent = root / "parent"
            production = "exporter/exporterhelper/internal/queue/cond.go"
            test = "exporter/exporterhelper/internal/queue/cond_test.go"
            for name in (production, test):
                target = parent / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("original")
            archive = root / "worker.tar"
            with tarfile.open(archive, "w") as output:
                for name, data in (
                    (production, b"equivalent implementation"),
                    (test, b"forged pass"),
                ):
                    entry = tarfile.TarInfo("workspace/" + name)
                    entry.size = len(data)
                    output.addfile(entry, io.BytesIO(data))
            frozen = root / "artifact"
            result = freeze_delta("otel-queue-cancellation", archive, parent, frozen)
            self.assertEqual(set(result["changed"]), {production})
            self.assertEqual(set(result["excluded_changes"]), {test})
            fresh = root / "fresh"
            shutil.copytree(parent, fresh)
            apply_delta("otel-queue-cancellation", frozen, fresh)
            self.assertEqual((fresh / production).read_text(), "equivalent implementation")
            self.assertEqual((fresh / test).read_text(), "original")
            (frozen / "files" / production).write_text("changed after capture")
            with self.assertRaisesRegex(ValueError, "changed after freezing"):
                apply_delta("otel-queue-cancellation", frozen, parent)

    def test_candidate_archive_aliases_and_duplicates_are_rejected(self) -> None:
        for kind in ("traversal", "symlink", "hardlink", "duplicate"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                parent = root / "parent"
                parent.mkdir()
                archive = root / "worker.tar"
                with tarfile.open(archive, "w") as output:
                    entry = tarfile.TarInfo(
                        "workspace/../escape" if kind == "traversal" else "workspace/cond.go"
                    )
                    if kind in {"symlink", "hardlink"}:
                        entry.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
                        entry.linkname = "/outside/answer"
                    output.addfile(entry)
                    if kind == "duplicate":
                        output.addfile(entry)
                with self.assertRaises(ValueError):
                    freeze_delta("otel-queue-cancellation", archive, parent, root / "artifact")

    def test_binary_capture_and_fast_output_overrun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "capture"
            execution = bounded_process(
                [sys.executable, "-c", "import sys;sys.stdout.buffer.write(bytes([0,255,10]))"],
                Path(directory).resolve(),
                {},
                stdout_path=path,
            )
            self.assertEqual(execution.returncode, 0)
            self.assertEqual(path.read_bytes(), bytes([0, 255, 10]))
            self.assertEqual(execution.stdout, "")
            limited = bounded_process(
                [sys.executable, "-c", "print('x'*100)"],
                Path(directory).resolve(),
                {},
                max_output=1,
            )
            self.assertTrue(limited.output_limited)
            strict = Path(directory).resolve() / "strict"
            physical = bounded_process(
                [sys.executable, "-c", "print('x'*20000)"],
                Path(directory).resolve(),
                {},
                max_output=4096,
                stdout_path=strict,
                enforce_output_files=True,
            )
            self.assertNotEqual(physical.returncode, 0)
            self.assertLessEqual(strict.stat().st_size, 4096)

    def test_runtime_grants_cannot_alias_curator_or_controller_trees(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            curator = root / "curator"
            exposed = curator / "fixed"
            (exposed / "bin").mkdir(parents=True)
            alias = root / "pretend-tools"
            alias.symlink_to(exposed, target_is_directory=True)
            for path in (exposed, alias):
                with self.assertRaisesRegex(ValueError, "overlaps"):
                    checked_toolchains([path], [curator])

    def test_streamed_hash_supports_large_dependencies_without_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            data = root / "data"
            with data.open("wb") as output:
                output.truncate(21_000_000)
            self.assertEqual(len(hash_regular(data, limit=22_000_000)), 64)
            alias = root / "alias"
            alias.symlink_to(data)
            with self.assertRaises(OSError):
                hash_regular(alias, limit=22_000_000)
            os.link(data, root / "hardlink")
            with self.assertRaises(ValueError):
                hash_regular(data, limit=22_000_000)

    def test_environment_failure_stays_distinct_from_candidate_behavior(self) -> None:
        command = {"name": "required", "status": "environment_failure", "checks": {}}
        grade = grade_record("case", {"status": "environment_failure", "commands": [command]})
        self.assertEqual(grade["status"], "harness_error")
        self.assertFalse(grade["objective_complete"])
        self.assertEqual(grade["failures"], [])
        command["status"] = "behavior_mismatch"
        grade = grade_record("case", {"status": "behavior_mismatch", "commands": [command]})
        self.assertEqual(grade["status"], "failed")
        self.assertIsNone(grade["harness_error"])
        self.assertEqual(grade["failures"], ["required"])

    def test_real_candidate_compiler_error_is_not_an_environment_failure(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "broken.c"
            source.write_text("int broken( { return 1; }\n")
            result = bounded_process([compiler, "-c", str(source)], root, {"PATH": "/usr/bin:/bin"})
            command = Command("build", result.argv, root)
            self.assertTrue(candidate_compile_failure(command, result, scored=True))
            self.assertFalse(candidate_compile_failure(command, result, scored=False))
            self.assertFalse(candidate_compile_failure(command, result, scored=True, oom=True))
            grade = grade_record(
                "case",
                {
                    "status": "candidate_failure",
                    "commands": [
                        {**result.to_dict(), "name": "build", "status": "candidate_build_failure"}
                    ],
                },
            )
            self.assertEqual(grade["status"], "failed")
            self.assertIsNone(grade["harness_error"])
            self.assertEqual(grade["failures"], ["build"])

    def test_signal_identifiers_and_compiler_crashes_have_distinct_classifications(
        self,
    ) -> None:
        command = Command("compile-queue", ["go", "test", "-c"], Path("/tmp"))
        result = Execution(
            command.argv,
            1,
            "",
            "cond_test.go:61:4: c.Signal undefined (type *cond has no field or method Signal)",
            1,
        )
        self.assertTrue(candidate_compile_failure(command, result, scored=True))
        for error in (
            "foo.c:1: internal compiler error: crash",
            "panic: compiler crashed\nfoo.go:1:1:",
            "cc1: fatal error: Killed signal terminated program cc1",
        ):
            result.stderr = error
            self.assertFalse(candidate_compile_failure(command, result, scored=True))

    def test_cancelled_set_does_not_start_another_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "set"

            def cancelled(case: dict[str, object], *_args: object) -> dict[str, object]:
                return {"case_id": case["id"], "status": "cancelled"}

            with patch("benchmarks.large_projects.__main__.qualify", side_effect=cancelled) as call:
                with self.assertRaises(SystemExit) as stopped:
                    large_main(
                        [
                            "qualify",
                            "--case",
                            "cpython-import-locks",
                            "--case",
                            "otel-queue-cancellation",
                            "--prepared",
                            str(root.parent),
                            "--output",
                            str(root),
                        ]
                    )
            self.assertEqual(stopped.exception.code, 130)
            self.assertEqual(call.call_count, 1)
            rows = json.loads((root / "report.json").read_text())
            self.assertEqual([row["status"] for row in rows], ["cancelled", "not_started"])

    def test_cancellation_survives_cleanup_failure_and_stops_the_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with patch("benchmarks.large_projects.deadline.multiprocessing.get_context") as context:
                process = context.return_value.Process.return_value
                process.join.side_effect = KeyboardInterrupt
                process.is_alive.return_value = False
                with patch(
                    "benchmarks.large_projects.deadline.cleanup_owned",
                    return_value={
                        "complete": False,
                        "errors": ["runtime unavailable"],
                        "removed": [],
                    },
                ):
                    result = supervise(root / "attempt", 10, lambda _d, _o: {})
            self.assertEqual(result["status"], "harness_error")
            self.assertTrue(result["operator_cancelled"])
            with patch(
                "benchmarks.large_projects.__main__.qualify",
                return_value={**result, "case_id": "cpython-import-locks"},
            ) as qualify:
                with self.assertRaises(SystemExit) as stopped:
                    large_main(
                        [
                            "qualify",
                            "--case",
                            "cpython-import-locks",
                            "--case",
                            "otel-queue-cancellation",
                            "--prepared",
                            str(root),
                            "--output",
                            str(root / "set"),
                        ]
                    )
            self.assertEqual(stopped.exception.code, 130)
            self.assertEqual(qualify.call_count, 1)

    def test_missing_runtime_gates_block_planning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "runtime.json").write_text(json.dumps({"status": "passed", "gates": {}}))
            context = root / "context.json"
            context.write_text(
                json.dumps(
                    {
                        "prepared": str(root),
                        "qualification": str(root),
                        "toolchains": [],
                        "runtime_qualification": str(root / "runtime.json"),
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "runtime qualification"):
                load_context(context, ["otel-queue-cancellation"])

    def test_refreshing_a_valid_same_parent_bundle_invalidates_the_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            case = case_at("otel-queue-cancellation")
            bundle = root / "bundle"
            module = bundle / "inputs/cache/go-mod/example.mod"
            module.parent.mkdir(parents=True)
            module.write_text("dependency one")

            def seal_bundle() -> None:
                (bundle / "dependencies.json").write_text(
                    json.dumps(
                        {
                            "case_id": case["id"],
                            "parent": case["parent"],
                            "status": "prefetched",
                            "paths": ["cache/go-mod"],
                            "hashes": tree_hashes(bundle / "inputs"),
                        }
                    )
                )

            seal_bundle()
            identity = verify_bundle(case, bundle)
            runtime = root / "runtime.json"
            runtime.write_text("{}")
            qualified = root / "qualified" / case["id"]
            qualified.mkdir(parents=True)
            (qualified / "qualification.json").write_text(
                json.dumps(
                    {
                        "status": "qualified",
                        "runner_hashes": harness_hashes(),
                        "sides": {"parent": {"dependencies": identity}},
                    }
                )
            )
            (qualified / "evidence-sha256.json").write_text(
                json.dumps({"qualification.json": hash_regular(qualified / "qualification.json")})
            )
            plan = {
                "entries": [{"case_id": case["id"]}],
                "large_context": {
                    "runtime_qualification": str(runtime),
                    "runtime_receipt_sha256": hash_regular(runtime),
                    "qualification": str(qualified.parent),
                    "qualification_receipts": {
                        case["id"]: hash_regular(qualified / "evidence-sha256.json")
                    },
                    "dependencies": {case["id"]: str(bundle)},
                    "dependency_identities": {case["id"]: identity},
                },
            }
            validate_context(plan)
            module.write_text("dependency two")
            seal_bundle()
            self.assertNotEqual(verify_bundle(case, bundle), identity)
            with self.assertRaisesRegex(ValueError, "dependency inputs changed"):
                validate_context(plan)

    def test_budget_child_uses_first_header_not_inherited_parent(self) -> None:
        root = {"type": "session_meta", "payload": {"id": "root", "source": "exec"}}
        child = {
            "type": "session_meta",
            "payload": {
                "id": "child",
                "source": {"subagent": {"thread_spawn": {"parent_thread_id": "root"}}},
            },
        }

        def usage(value: int) -> dict[str, object]:
            return {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": value}},
                },
            }

        evidence = {
            "readonly_unchanged": True,
            "outside_unchanged": True,
            "returncode": 1,
            "stdout": json.dumps(
                {
                    "type": "turn.failed",
                    "error": {"message": "shared rollout token budget exhausted"},
                }
            ),
            "sessions": [{"events": [root, usage(10)]}, {"events": [child, root, usage(60)]}],
        }
        self.assertEqual(validate_native(evidence, "budget")["overshoot_units"], 20)
        evidence["sessions"] = [{"events": [root, usage(70)]}]
        with self.assertRaises(ValueError):
            validate_native(evidence, "budget")


def kernel_available() -> bool:
    """CI absence is a disclosed skip, never a qualification receipt."""
    if (
        sys.platform != "linux"
        or not shutil.which("docker")
        or not Path("/var/run/docker.sock").exists()
    ):
        return False
    try:
        return docker(["image", "inspect", IMAGE], timeout=5).returncode == 0
    except (OSError, ValueError):
        return False


@unittest.skipUnless(
    kernel_available(), "requires local Linux Docker and the pinned image; not qualified here"
)
class KernelBoundaryTests(unittest.TestCase):
    """Actual kernel controls; these do not mock resource limits or timeout cleanup."""

    def test_aggregate_limits_freeze_and_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controls = kernel_controls(
                Path(directory).resolve() / "controls", str(uuid.uuid4()), Deadline(90)
            )
            self.assertEqual(len(controls), 6)
            self.assertTrue(all(c["status"] == "passed" for c in controls.values()))

    def test_staging_timeout_and_external_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controls = watchdog_controls(Path(directory).resolve())
            self.assertEqual(set(controls), {"staging_deadline", "cancellation_cleanup"})
            self.assertTrue(all(c["status"] == "passed" for c in controls.values()))

    def test_authoritative_inputs_are_readonly_in_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            seed = root / "seed"
            seed.mkdir()
            (seed / "hidden").write_text("authoritative")
            limits = Limits(memory_bytes=128 * 1024**2, filesystem_bytes=128 * 1024**2)
            with ResourceCell(root / "cell", limits, native_sandbox=True) as cell:
                source = cell.root / "source"
                cell.upload(seed, source)
                script = """import pathlib,errno,sys
p=pathlib.Path(sys.argv[1]);assert p.read_text()=='authoritative'
try:p.write_text('forged')
except OSError as e:assert e.errno==errno.EROFS
else:raise AssertionError('authoritative fixture was writable')
"""
                result = evaluator_command(
                    cell,
                    ["/usr/bin/python3", "-I", "-B", "-c", script, str(source / "hidden")],
                    source,
                    source,
                    "otel-queue-cancellation",
                    "test",
                    "required",
                    {"PATH": "/usr/bin:/bin"},
                    10,
                )
                require(result)
                self.assertEqual(
                    require(cell.execute(["/bin/cat", str(source / "hidden")])).stdout,
                    "authoritative",
                )
                cell.freeze()
                with patch("benchmarks.large_projects.resources.shutil.disk_usage") as disk:
                    disk.return_value.free = 0
                    with self.assertRaisesRegex(ValueError, "insufficient controller disk"):
                        cell.download(source, root / "snapshot.tar")
                self.assertFalse((root / "snapshot.tar").exists())
            self.assertEqual(tree_hashes(seed).keys(), {"hidden"})
