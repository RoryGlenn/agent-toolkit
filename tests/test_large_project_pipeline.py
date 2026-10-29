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

from benchmarks.files import hash_regular
from benchmarks.large_projects.artifacts import apply_delta, freeze_delta, tree_hashes
from benchmarks.large_projects.candidate import grade_record, load_context
from benchmarks.large_projects.integration import evaluator_command
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
from benchmarks.process import bounded_process


class PipelineDataTests(unittest.TestCase):
    """Archive data and incomplete checks cannot become authoritative passing evidence."""

    def test_frozen_delta_restores_authoritative_tests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
                root = Path(directory)
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
            path = Path(directory) / "capture"
            execution = bounded_process(
                [sys.executable, "-c", "import sys;sys.stdout.buffer.write(bytes([0,255,10]))"],
                Path(directory),
                {},
                stdout_path=path,
            )
            self.assertEqual(execution.returncode, 0)
            self.assertEqual(path.read_bytes(), bytes([0, 255, 10]))
            self.assertEqual(execution.stdout, "")
            limited = bounded_process(
                [sys.executable, "-c", "print('x'*100)"], Path(directory), {}, max_output=1
            )
            self.assertTrue(limited.output_limited)
            strict = Path(directory) / "strict"
            physical = bounded_process(
                [sys.executable, "-c", "print('x'*20000)"],
                Path(directory),
                {},
                max_output=4096,
                stdout_path=strict,
                enforce_output_files=True,
            )
            self.assertNotEqual(physical.returncode, 0)
            self.assertLessEqual(strict.stat().st_size, 4096)

    def test_runtime_grants_cannot_alias_curator_or_controller_trees(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
            root = Path(directory)
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

    def test_missing_runtime_gates_block_planning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
                Path(directory) / "controls", str(uuid.uuid4()), Deadline(90)
            )
            self.assertEqual(len(controls), 6)
            self.assertTrue(all(c["status"] == "passed" for c in controls.values()))

    def test_staging_timeout_and_external_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controls = watchdog_controls(Path(directory))
            self.assertEqual(set(controls), {"staging_deadline", "cancellation_cleanup"})
            self.assertTrue(all(c["status"] == "passed" for c in controls.values()))

    def test_authoritative_inputs_are_readonly_in_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
            self.assertEqual(tree_hashes(seed).keys(), {"hidden"})
