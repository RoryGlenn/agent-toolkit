"""Exercise portable metadata and inventory failures without relying on prose shape."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from typing import Any

import authoring

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "standards/authoring/templates"


class AuthoringTests(unittest.TestCase):
    """Test actual parser and inventory boundaries, including valid alternatives."""

    def setUp(self) -> None:
        """Create an isolated artifact and evidence inventory."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "skills/example-skill/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text(
            "---\nname: example-skill\ndescription: Handle example requests.\n---\nDo the task.\n",
            encoding="utf-8",
        )
        self.catalog = self.root / authoring.CATALOG
        self.catalog.parent.mkdir(parents=True)
        self.data: dict[str, Any] = {
            "schema": authoring.SCHEMA,
            "standard_version": authoring.STANDARD_VERSION,
            "artifacts": [
                {
                    "path": "skills/example-skill/SKILL.md",
                    "basis": "Original example workflow.",
                    "evidence": [],
                    "assessment": "not_assessed",
                    "next_check": "Exercise an example request and an adjacent request.",
                }
            ],
        }

    def metadata_report(self, text: str) -> authoring.Report:
        """Check supplied metadata in the example skill's real directory."""
        self.skill.write_text(text, encoding="utf-8")
        report = authoring.Report()
        authoring.check_skill(self.skill, report)
        return report

    def catalog_report(self, expected: set[str] | None = None) -> authoring.Report:
        """Check the current isolated catalog against its expected package paths."""
        self.catalog.write_text(json.dumps(self.data), encoding="utf-8")
        report = authoring.Report()
        authoring.check_catalog(
            self.root,
            expected if expected is not None else {"skills/example-skill/SKILL.md"},
            report,
        )
        return report

    def test_current_repository_has_complete_inventory(self) -> None:
        """Check the real inventory without asserting that its artifacts behave well."""
        report = authoring.check(ROOT)
        self.assertEqual(report.errors, [])
        self.assertGreater(report.covered_artifacts, 0)
        self.assertEqual(report.behavior_assessment, "not_performed")

    def test_multiline_yaml_and_supported_optional_fields(self) -> None:
        """Accept ordinary YAML variants and preserve a small free-form body."""
        report = self.metadata_report(
            "---\nname: example-skill\ndescription: >\n  Handle example requests\n"
            "  with optional resources.\ncompatibility: Python 3.11\nlicense: Proprietary\n"
            "allowed-tools: Read\nmetadata:\n  version: '1'\n---\nA useful procedure.\n"
        )
        self.assertEqual(report.errors, [])

    def test_duplicate_keys_fail_even_when_last_value_is_valid(self) -> None:
        """Prevent conflicting descriptions from silently passing authoring checks."""
        report = self.metadata_report(
            "---\nname: example-skill\ndescription: First\ndescription: Second\n---\nTask.\n"
        )
        self.assertTrue(report.errors)

    def test_invalid_types_limits_and_missing_body(self) -> None:
        """Reject malformed portable fields with useful failures instead of crashes."""
        cases = [
            "name: wrong-name\ndescription: Valid",
            "name: example-skill\ndescription: true",
            "name: example-skill\ndescription: [a, b]",
            "name: example-skill\ndescription: " + "x" * 1025,
            "name: example-skill\ndescription: Valid\ncompatibility: " + "x" * 501,
            "name: example-skill\ndescription: Valid\nmetadata:\n  version: 1",
            "name: example-skill\ndescription: Valid\nallowed-tools: [Read]",
        ]
        for fields in cases:
            with self.subTest(fields=fields[:100]):
                self.assertTrue(self.metadata_report(f"---\n{fields}\n---\nTask.\n").errors)
        self.assertTrue(
            self.metadata_report("---\nname: example-skill\ndescription: OK\n---\n").errors
        )

    def test_large_entrypoint_is_advisory(self) -> None:
        """Keep an upstream recommendation separate from mandatory syntax."""
        text = self.skill.read_text(encoding="utf-8") + "Detail.\n" * 501
        report = self.metadata_report(text)
        self.assertFalse(report.errors)
        self.assertTrue(report.warnings)

    def test_inventory_accepts_explicit_evaluation_gap(self) -> None:
        """Allow honest legacy adoption without inventing completed evaluations."""
        report = self.catalog_report()
        self.assertFalse(report.errors)
        self.assertEqual(report.covered_artifacts, 1)

    def test_missing_duplicate_and_stale_entries_fail(self) -> None:
        """Require exact inventory coverage as packages are added or removed."""
        self.assertTrue(self.catalog_report({"skills/new-skill/SKILL.md"}).errors)
        self.data["artifacts"].append(self.data["artifacts"][0].copy())
        self.assertTrue(self.catalog_report().errors)

    def test_evidence_must_exist_and_remain_within_checkout(self) -> None:
        """Reject dangling references, traversal, and symlinks to external evidence."""
        entry = self.data["artifacts"][0]
        for value in (
            "missing.txt",
            "../outside.txt",
            str(self.skill),
            "./skills/example-skill/SKILL.md",
        ):
            with self.subTest(value=value):
                entry["evidence"] = [value]
                self.assertTrue(self.catalog_report().errors)
        link = self.root / "external"
        link.symlink_to(ROOT / "README.md")
        entry["evidence"] = ["external"]
        self.assertTrue(self.catalog_report().errors)
        entry["evidence"] = ["skills/example-skill/SKILL.md"]
        self.assertFalse(self.catalog_report().errors)

    def test_cyclic_evidence_symlink_returns_diagnostic(self) -> None:
        """Reject unresolvable evidence links without a parser traceback."""
        (self.root / "cycle").symlink_to("cycle")
        self.data["artifacts"][0]["evidence"] = ["cycle"]
        self.assertTrue(self.catalog_report().errors)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX named pipes")
    def test_invalid_source_tree_fails_before_opening_fifo(self) -> None:
        """Exit promptly when installer validation rejects a nonregular skill file."""
        self.skill.unlink()
        os.mkfifo(self.skill)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "authoring.py"),
                "check",
                "--root",
                str(self.root),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertTrue(json.loads(result.stdout)["errors"])

    def test_checker_cannot_upgrade_behavioral_assessment(self) -> None:
        """Prevent a format-only catalog from claiming certification."""
        self.data["artifacts"][0]["assessment"] = "community_approved"
        self.assertTrue(self.catalog_report().errors)

    def test_reviewed_entry_requires_an_existing_review_record(self) -> None:
        """Require a review reference without presenting it as a favorable verdict."""
        entry = self.data["artifacts"][0]
        entry["assessment"] = "reviewed"
        self.assertTrue(self.catalog_report().errors)
        record = self.root / "review.md"
        record.write_text("Verdict: needs_change. Observed task failure.\n", encoding="utf-8")
        entry["review_record"] = "review.md"
        self.assertFalse(self.catalog_report().errors)

    def test_review_fingerprint_detects_changed_artifact(self) -> None:
        """Reject stale review identity without pretending to judge semantic quality."""
        entry = self.data["artifacts"][0]
        entry["assessment"] = "reviewed"
        (self.root / "review.md").write_text("Verdict: ready_with_limits.\n")
        entry["review_record"] = "review.md"
        entry["reviewed_sha256"] = hashlib.sha256(self.skill.read_bytes()).hexdigest()
        self.assertFalse(self.catalog_report().errors)
        self.skill.write_text(self.skill.read_text() + "Changed behavior.\n")
        self.assertTrue(any("artifact changed" in error for error in self.catalog_report().errors))
        entry["reviewed_sha256"] = hashlib.sha256(self.skill.read_bytes()).hexdigest()
        self.assertFalse(self.catalog_report().errors)

    def test_review_fingerprint_rejects_malformed_values_and_missing_files(self) -> None:
        """An optional identity must be valid and cannot hide a missing artifact."""
        entry = self.data["artifacts"][0]
        for value in (None, 1, "", "x" * 64, "a" * 63):
            with self.subTest(value=value):
                entry["reviewed_sha256"] = value
                self.assertTrue(self.catalog_report().errors)
        entry["reviewed_sha256"] = hashlib.sha256(self.skill.read_bytes()).hexdigest()
        self.skill.unlink()
        self.assertTrue(self.catalog_report().errors)

    def test_malformed_catalog_returns_diagnostic(self) -> None:
        """Report invalid JSON rather than leaving an unhandled parser traceback."""
        self.catalog.write_text("{", encoding="utf-8")
        report = authoring.Report()
        authoring.check_catalog(self.root, set(), report)
        self.assertTrue(report.errors)

    def test_cli_reports_structure_separately(self) -> None:
        """Expose machine-readable diagnostics with an honest assessment boundary."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = authoring.main(["check", "--root", str(ROOT), "--json"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue())["behavior_assessment"], "not_performed")

    def test_templates_render_into_supported_formats(self) -> None:
        """Exercise template parsing without requiring a particular instruction wording."""
        values = {
            "skill_name": "example-skill",
            "agent_identifier": "example_agent",
            "agent_display_name": "Example Agent",
        }

        def render(filename: str) -> str:
            """Substitute representative plain-text values for every template field."""
            return re.sub(
                r"\{\{([^{}]+)\}\}",
                lambda match: values.get(match[1], "Example task-specific guidance."),
                (TEMPLATES / filename).read_text(encoding="utf-8"),
            )

        self.assertFalse(self.metadata_report(render("SKILL.md.template")).errors)
        role = tomllib.loads(render("codex-agent.toml.template"))
        self.assertEqual(role["name"], "example_agent")
        self.assertTrue(role["developer_instructions"].strip())
        evaluation = json.loads(render("evals.json.template"))
        self.assertEqual(evaluation["skill_name"], "example-skill")
        self.assertTrue(evaluation["evals"])


if __name__ == "__main__":
    unittest.main()
