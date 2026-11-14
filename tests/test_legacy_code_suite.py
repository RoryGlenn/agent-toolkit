"""Validate declared coverage, real selection/restore, and trusted behavior controls."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import install
import project_bootstrap as project
from skill_authoring.workflow import cases

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/legacy-code-skill"


def fixture_module(name: str):  # type: ignore[no-untyped-def]
    """Import only the repository's inspected original fixtures, not model output."""
    spec = importlib.util.spec_from_file_location(name, SKILL / "evals/fixtures" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LegacyCodeCoverageTests(unittest.TestCase):
    """Check traceability structure; source truth and model quality need separate evidence."""

    def test_declared_source_scope_and_evaluation_links(self) -> None:
        coverage = json.loads((SKILL / "references/coverage.json").read_text())
        self.assertEqual(coverage["schema"], "legacy-code-source-coverage/v1")
        self.assertEqual(coverage["source"]["isbn"], "9780132931755")
        self.assertRegex(coverage["source"]["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual([c["chapter"] for c in coverage["chapters"]], list(range(1, 26)))
        self.assertEqual([t["number"] for t in coverage["techniques"]], list(range(1, 25)))
        name, domain = cases((SKILL / "evals/evals.json").resolve(), SKILL.resolve())
        self.assertEqual(name, "legacy-code-skill")
        integrations = json.loads((SKILL / "evals/integration-cases.json").read_text())["cases"]
        case_ids = {c["case_id"] for c in domain + integrations}
        self.assertTrue({f"LC{n:02}" for n in range(1, 13)}.issubset(case_ids))
        for entry in coverage["chapters"] + coverage["techniques"]:
            self.assertEqual(entry["study_status"], "studied")
            self.assertTrue(entry["source_refs"])
            self.assertTrue(entry["evaluation_gap"])
            self.assertTrue(set(entry["evaluation_ids"]).issubset(case_ids))
            for ref in entry["source_refs"]:
                self.assertRegex(ref, r"^OEBPS/html/ch\d{2}\.html(?:#[A-Za-z0-9]+)?$")
            for path in entry["guidance"]:
                self.assertTrue((SKILL / path).resolve().is_relative_to(SKILL.resolve()))
                self.assertTrue((SKILL / path).is_file())
        self.assertEqual(
            next(c for c in domain if c["case_id"] == "LC05")["invocation"], "implicit"
        )


class LegacyCodeInstallationTests(unittest.TestCase):
    """Exercise actual selected installation and portable copied projects in isolated roots."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.home, self.client = self.base / "home", self.base / "home/.codex"
        redirect = contextlib.redirect_stdout(io.StringIO())
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def test_selected_install_restore_protects_shared_routing_and_private_library(self) -> None:
        install.install(ROOT, "codex", ["software-design-skill"], self.home, self.client)
        library = self.home / ".local/share/legacy-code-specialist"
        library.mkdir(parents=True)
        (library / "notes.json").write_text('"unrelated private study"')
        receipt = install.install(ROOT, "codex", ["legacy-code-skill"], self.home, self.client)
        self.assertIsNotNone(receipt)
        self.assertEqual(json.loads(receipt.read_text())["state"], "installed")
        self.assertEqual(
            {p.name for p in (self.home / ".agents/skills").iterdir()},
            {"legacy-code-skill", "task-routing-skill", "software-design-skill"},
        )
        role = self.client / "agents/legacy-code-agent.toml"
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(ROOT / "agents/codex/legacy-code-agent.toml"))
        self.assertFalse(list((self.home / ".agents/skills/legacy-code-skill").rglob("*.epub")))
        self.assertIsNone(
            install.install(ROOT, "codex", ["legacy-code-skill"], self.home, self.client)
        )
        install.restore(receipt)
        self.assertFalse((self.home / ".agents/skills/legacy-code-skill").exists())
        self.assertTrue((self.home / ".agents/skills/task-routing-skill").exists())
        self.assertTrue((self.client / "agents/software-design-agent.toml").exists())
        self.assertEqual((library / "notes.json").read_text(), '"unrelated private study"')

    def test_selected_project_relocates_and_refuses_edited_owned_content(self) -> None:
        app = self.base / "app"
        available = install.inventory(ROOT)
        arguments = (ROOT, app, available, install.AGENTS, install.IGNORED)
        project.bootstrap(*arguments, skills=["legacy-code-skill"], target="codex", dry_run=True)
        self.assertFalse(app.exists())
        project.bootstrap(*arguments, skills=["legacy-code-skill"], target="both")
        manifest = json.loads((app / project.MANIFEST).read_text())
        self.assertEqual(manifest["skills"], ["legacy-code-skill", "task-routing-skill"])
        self.assertEqual(len(list((app / ".codex/agents").iterdir())), 1)
        self.assertFalse((app / ".github/agents").exists())
        self.assertFalse(list(app.rglob("*.epub")))
        self.assertFalse(any(p.is_symlink() for p in app.rglob("*")))
        moved = self.base / "moved"
        app.rename(moved)
        project.bootstrap(ROOT, moved, available, install.AGENTS, install.IGNORED)
        owned = moved / ".agents/skills/legacy-code-skill/SKILL.md"
        owned.write_text(owned.read_text() + "\nProject customization.\n")
        with self.assertRaisesRegex(project.BootstrapError, "edited or removed"):
            project.bootstrap(ROOT, moved, available, install.AGENTS, install.IGNORED, update=True)
        self.assertTrue(owned.read_text().endswith("Project customization.\n"))

    def test_default_profile_stays_optional_and_full_catalog_includes_legacy(self) -> None:
        self.assertNotIn("legacy-code-skill", project.DEFAULT_SKILLS)
        self.assertEqual(
            project.resolve_skills(["legacy-code-skill"], install.inventory(ROOT)),
            ["legacy-code-skill", "task-routing-skill"],
        )
        self.assertIn("legacy-code-skill", install.inventory(ROOT))
        self.assertEqual(install.AGENTS["codex"]["legacy-code-skill"], ["legacy-code-agent.toml"])
        receipt = install.install(ROOT, "copilot", ["legacy-code-skill"], self.home, self.client)
        self.assertIsNotNone(receipt)
        self.assertTrue((self.home / ".copilot/skills/legacy-code-skill").is_symlink())
        self.assertFalse((self.home / ".copilot/agents").exists())


class LegacyCaseOracleTests(unittest.TestCase):
    """Show trusted controls are distinguishable; these are not model evaluations."""

    def assert_export_contract(self, operation, audit) -> None:  # type: ignore[no-untyped-def]
        with tempfile.TemporaryDirectory() as temporary:
            audit.clear()
            destination = Path(temporary) / "rows.csv"
            self.assertEqual(operation([("b", 2, "1.005"), ("a", 1, "2.00")], destination), 402)
            self.assertTrue(destination.is_file(), "The effect must happen, not just the return")
            self.assertEqual(destination.read_bytes(), b"b,2,101\na,1,200\n")
            self.assertEqual(audit, [(str(destination), 402)])
            audit.clear()
            with self.assertRaises(OSError):
                operation([("b", 2, "1.005"), ("a", 1, "2.00")], Path(temporary))
            self.assertEqual(audit, [], "Failed writes must not emit a success audit")

    def test_export_correct_and_lost_or_reordered_effect_controls(self) -> None:
        billing = fixture_module("billing")
        self.assert_export_contract(billing.export_invoice, billing.AUDIT)
        with self.assertRaises(AssertionError):
            self.assert_export_contract(lambda rows, path: 402, billing.AUDIT)
        with self.assertRaises(AssertionError):
            self.assert_export_contract(
                lambda rows, path: billing.export_invoice(sorted(rows), path), billing.AUDIT
            )

    def test_export_oracle_rejects_missing_success_and_false_failure_audits(self) -> None:
        billing = fixture_module("billing")

        def omit_audit(rows, destination):  # type: ignore[no-untyped-def]
            total = billing.export_invoice(rows, destination)
            billing.AUDIT.clear()
            return total

        def audit_failure(rows, destination):  # type: ignore[no-untyped-def]
            try:
                return billing.export_invoice(rows, destination)
            except OSError:
                billing.AUDIT.append((str(destination), 402))
                raise

        for operation in [omit_audit, audit_failure]:
            with self.assertRaises(AssertionError):
                self.assert_export_contract(operation, billing.AUDIT)

    def assert_selection_contract(self, select) -> None:  # type: ignore[no-untyped-def]
        class FalseConnection:
            def __bool__(self) -> bool:
                return False

        real, supplied = object(), FalseConnection()
        calls = []

        def connect() -> object:
            calls.append("connect")
            return real

        self.assertIs(select(supplied, connect), supplied)
        self.assertEqual(calls, [])
        self.assertIs(select(None, connect), real)
        self.assertEqual(calls, ["connect"])

    def test_constructor_selection_correct_and_falsy_dependency_wrong_control(self) -> None:
        self.assert_selection_contract(
            lambda supplied, connect: connect() if supplied is None else supplied
        )
        with self.assertRaises(AssertionError):
            self.assert_selection_contract(lambda supplied, connect: supplied or connect())

    def assert_discount_contract(self, discount) -> None:  # type: ignore[no-untyped-def]
        for cents, percent, expected in [
            (105, 10, 94),
            (100, 10, 90),
            (105, 0, 105),
            (105, 100, 0),
        ]:
            self.assertEqual(discount(cents, percent), expected)
        for cents, percent in [(-1, 0), (100, -1), (100, 101)]:
            with self.assertRaises(ValueError):
                discount(cents, percent)

    def test_approved_discount_correction_distinguishes_defective_baseline(self) -> None:
        def corrected(cents: int, percent: int) -> int:
            if cents < 0 or not 0 <= percent <= 100:
                raise ValueError("Invalid price or percent")
            amount = (Decimal(cents) * Decimal(percent) / 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            return cents - int(amount)

        self.assert_discount_contract(corrected)
        baseline = fixture_module("discount").discounted
        self.assertEqual(baseline(105, 10), 95)
        with self.assertRaises(AssertionError):
            self.assert_discount_contract(baseline)


if __name__ == "__main__":
    unittest.main()
