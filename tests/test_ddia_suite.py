"""Exercise portable DDIA routing, evidence integrity and installation behavior."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import install
import project_bootstrap

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "skills/ddia-skill"


def module(name: str) -> ModuleType:
    """Load one shipped helper without changing global import search paths."""
    spec = importlib.util.spec_from_file_location(
        f"ddia_suite_{name}", SHARED / f"{'evals' if name == 'evaluate' else 'scripts'}/{name}.py"
    )
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


guide = module("guide")
evaluate = module("evaluate")
experiments = module("experiments")
book = module("book")


class DDIASuiteTests(unittest.TestCase):
    """Verify behavior from installed resources rather than matching prose wording."""

    def setUp(self) -> None:
        """Allocate owned disposable package and host roots."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()

    def test_routes_select_useful_concepts_and_show_only_requested_section(self) -> None:
        """Routing works without a private book and preserves qualified worked examples."""
        matches = guide.route("offline concurrent edits", workflow="design")
        self.assertIn("multi-leader-sync", {match["id"] for match in matches})
        concept = next(c for c in guide.load()["concepts"] if c["id"] == "write-skew")
        section = guide.concept_text(SHARED, concept)
        self.assertIn("Snapshot isolation", section)
        self.assertNotIn("## Atomic commit and coordinator recovery", section)
        with self.assertRaises(ValueError):
            guide.route("the and")

    def test_explanations_route_across_all_chapters(self) -> None:
        """A teaching request can retrieve every domain instead of only data models."""
        for concept in guide.load()["concepts"]:
            with self.subTest(concept=concept["id"]):
                matches = guide.route(concept["title"], workflow="explain", limit=20)
                self.assertIn(concept["id"], {match["id"] for match in matches})
        matches = guide.route("old lease owner fencing", workflow="explain")
        self.assertIn("leases-fencing", {match["id"] for match in matches})

    def test_all_authored_locators_resolve_against_the_actual_bundled_source(self) -> None:
        """A mistyped or stale concept anchor fails against real EPUB chapter structure."""
        corpus = book.extract(ROOT / "books/designing-data-intensive-applications-2nd-edition.epub")
        index = self.base / "actual-index.json"
        index.write_text(json.dumps(corpus))
        self.assertTrue(guide.check(SHARED, index)["source_checked"])

    def test_coverage_validates_source_links_and_rejects_unknown_or_changed_inputs(self) -> None:
        """All chapter links resolve, and corrupted or foreign source metadata fails."""
        copy = self.base / "shared"
        shutil.copytree(SHARED, copy, ignore=shutil.ignore_patterns("__pycache__"))
        result = guide.check(copy)
        self.assertEqual(result["chapters"], 14)
        self.assertFalse(result["source_checked"])
        ledger = guide.load(copy)
        index = self.base / "index.json"
        index.write_text(
            json.dumps(
                {
                    "source_sha256": ledger["source_sha256"],
                    "sections": [
                        {"ref": ref} for c in ledger["concepts"] for ref in c["source_refs"]
                    ],
                }
            )
        )
        self.assertTrue(guide.check(copy, index)["source_checked"])
        data = json.loads(index.read_text())
        data["sections"] = []
        index.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Unresolved source locator"):
            guide.check(copy, index)
        ledger["concepts"][0]["reference"] = "../external.md"
        (copy / "references/coverage.json").write_text(json.dumps(ledger))
        with self.assertRaisesRegex(ValueError, "Invalid package resource"):
            guide.check(copy)

    def test_each_workflow_installs_shared_skill_and_one_role_and_restores(self) -> None:
        """Selecting a workflow cannot silently omit its shared reference dependency."""
        for workflow in project_bootstrap.DDIA_WORKFLOWS:
            with self.subTest(workflow=workflow), contextlib.redirect_stdout(io.StringIO()):
                home = self.base / workflow
                receipt = install.install(
                    ROOT, "codex", [f"ddia-{workflow}-skill"], home, home / ".codex"
                )
                assert receipt is not None
                shared = home / ".agents/skills/ddia-skill"
                self.assertTrue((shared / "references/coverage.json").is_file())
                self.assertTrue((home / ".codex/agents/ddia-agent.toml").is_file())
                guide.check(shared)
                install.restore(receipt)
                self.assertFalse(shared.exists())

    def test_project_workflow_dependency_survives_relocation_without_personal_source(self) -> None:
        """Portable selection carries procedures, templates and helpers as regular files."""
        project = self.base / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            project_bootstrap.bootstrap(
                ROOT,
                project,
                install.inventory(ROOT),
                install.AGENTS,
                install.IGNORED,
                skills=["ddia-migrate-skill"],
                target="codex",
            )
        relocated = self.base / "relocated"
        project.rename(relocated)
        shared = relocated / ".agents/skills/ddia-skill"
        self.assertEqual(guide.check(shared)["chapters"], 14)
        self.assertTrue((shared / "assets/handoff.template.md").is_file())
        manifest = json.loads((relocated / project_bootstrap.MANIFEST).read_text())
        self.assertEqual(
            manifest["skills"], ["ddia-migrate-skill", "ddia-skill", "task-routing-skill"]
        )
        self.assertFalse(any(path.is_symlink() for path in relocated.rglob("*")))

    def test_missing_dependency_fails_before_install_or_project_write(self) -> None:
        """An incomplete toolkit is rejected rather than creating a broken workflow."""
        available = install.inventory(ROOT)
        del available["ddia-skill"]
        with self.assertRaisesRegex(project_bootstrap.BootstrapError, "missing required"):
            project_bootstrap.bootstrap(
                ROOT,
                self.base / "missing",
                available,
                install.AGENTS,
                install.IGNORED,
                skills=["ddia-design-skill"],
                target="codex",
            )
        self.assertFalse((self.base / "missing").exists())

    def test_every_experiment_rejects_broken_and_accepts_sufficient_control(self) -> None:
        """The actual SQLite and bounded-model oracles detect their introduced violation."""
        for name in experiments.EXPERIMENTS:
            with self.subTest(name=name):
                result = experiments.run(name)
                self.assertFalse(result["broken"]["invariant"])
                self.assertTrue(result["sufficient"]["invariant"])

    def test_admission_closes_setup_and_readback_connections(self) -> None:
        """Repeated experiments release database handles outside transaction context scope."""
        connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def track(database: Path, timeout: float = 5.0) -> sqlite3.Connection:
            connection = connect(database, timeout=timeout)
            if threading.current_thread() is threading.main_thread():
                opened.append(connection)
            return connection

        with patch.object(experiments.sqlite3, "connect", side_effect=track):
            experiments.run("atomic-admission")
        self.assertTrue(opened)
        for connection in opened:
            with self.assertRaisesRegex(sqlite3.ProgrammingError, "closed database"):
                connection.execute("SELECT 1")

    def make_plan(self) -> tuple[Path, dict[str, object]]:
        """Freeze a small repeated comparison from an explicit current package."""
        output = self.base / "comparison"
        result = evaluate.plan(
            output,
            SHARED,
            SHARED,
            selected=["harmless-retry"],
            trials=2,
            seed=17,
            model="recorded-model",
            effort="high",
            budget="equal test budget",
        )
        return output, result

    def test_comparison_freezes_matched_inputs_withholds_rubrics_and_reports_missing(self) -> None:
        """Three arms have identical tasks, explicit settings and no actor grading answers."""
        output, data = self.make_plan()
        self.assertEqual(len(data["runs"]), 6)
        tasks = set()
        for run in data["runs"]:
            actor = output / run["actor"]
            tasks.add((actor / "TASK.md").read_bytes())
            if run["arm"] == "baseline":
                self.assertFalse((actor / "resources").exists())
            else:
                catalog = json.loads((actor / "resources/ddia-skill/evals/cases.json").read_text())
                self.assertTrue(all("criteria" not in case for case in catalog["cases"]))
        self.assertEqual(len(tasks), 1)
        self.assertEqual(len(evaluate.report(output)["missing"]), 6)
        self.assertTrue(all(v["mean"] is None for v in evaluate.report(output)["arms"].values()))
        with self.assertRaises(FileExistsError):
            evaluate.plan(
                output,
                SHARED,
                SHARED,
                selected=[],
                trials=1,
                seed=0,
                model="same",
                effort="same",
                budget="same",
            )

    def test_semantic_scores_require_evidence_and_frozen_inputs(self) -> None:
        """Invalid scores, repeat receipts and changed actor files cannot quietly pass."""
        output, data = self.make_plan()
        run = data["runs"][0]
        response = self.base / "response.txt"
        response.write_bytes(b"Concrete observed response\r\n")
        scoring = self.base / "scores.json"
        scoring.write_text(json.dumps({f"c{i}": {"score": 2, "evidence": ""} for i in range(1, 5)}))
        with self.assertRaisesRegex(ValueError, "Invalid semantic review"):
            evaluate.record(output, run["id"], response, scoring, "independent")
        scoring.write_text(
            json.dumps(
                {f"c{i}": {"score": 2, "evidence": "Observed behavior"} for i in range(1, 5)}
            )
        )
        evaluate.record(output, run["id"], response, scoring, "independent")
        self.assertEqual(evaluate.report(output)["arms"][run["arm"]]["mean"], 1.0)
        with self.assertRaises(FileExistsError):
            evaluate.record(output, run["id"], response, scoring, "independent")
        (output / run["actor"] / "TASK.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "resources changed"):
            evaluate.report(output)

    def test_snapshot_rejects_linked_resources_and_output_overlap(self) -> None:
        """Planner inputs cannot pull arbitrary linked files into an actor snapshot."""
        source = self.base / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("test guidance")
        (source / "linked").symlink_to(ROOT / "README.md")
        with self.assertRaisesRegex(ValueError, "Non-regular"):
            evaluate.plan(
                self.base / "rejected",
                source,
                SHARED,
                selected=[],
                trials=1,
                seed=0,
                model="same",
                effort="same",
                budget="same",
            )
        self.assertFalse((self.base / "rejected").exists())
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            evaluate.plan(
                source / "nested",
                source,
                SHARED,
                selected=[],
                trials=1,
                seed=0,
                model="same",
                effort="same",
                budget="same",
            )


if __name__ == "__main__":
    unittest.main()
