"""Exercise curator source preparation without network or model calls."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from benchmarks.large_projects.prepare import CATALOG, prepare


class CuratorPreparationTests(unittest.TestCase):
    """Check source separation and fail-closed provenance gates."""

    def setUp(self) -> None:
        """Create an upstream fixture with separate production and test changes."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        self.run_git("init", "-q")
        (self.upstream / "module.txt").write_text("broken\n")
        (self.upstream / "tests.txt").write_text("old control\n")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "parent")
        parent = self.run_git("rev-parse", "HEAD").decode().strip()
        (self.upstream / "module.txt").write_text("fixed\n")
        (self.upstream / "tests.txt").write_text("new behavioral check\n")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "fixed")
        fixed = self.run_git("rev-parse", "HEAD").decode().strip()
        # Build the expected delta independently, not through the helper under test.
        old_blob = self.run_git("rev-parse", f"{parent}:tests.txt").decode().strip()
        new_blob = self.run_git("rev-parse", f"{fixed}:tests.txt").decode().strip()
        expected_patch = (
            f"diff --git a/tests.txt b/tests.txt\n"
            f"index {old_blob}..{new_blob} 100644\n"
            "--- a/tests.txt\n+++ b/tests.txt\n@@ -1 +1 @@\n"
            "-old control\n+new behavioral check\n"
        ).encode()
        self.case: dict[str, Any] = {
            "id": "fixture",
            "url": str(self.upstream),
            "parent": parent,
            "fixed": fixed,
            "test_paths": ["tests.txt"],
            "test_patch_sha256": hashlib.sha256(expected_patch).hexdigest(),
        }

    def run_git(self, *args: str) -> bytes:
        """Run fixture-only Git commands with explicit test identity.

        Parameters
        ----------
        args
            Git arguments.
        """
        return subprocess.check_output(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=/dev/null",
                *args,
            ],
            cwd=self.upstream,
            stderr=subprocess.PIPE,
        )

    def test_parent_keeps_broken_code_with_same_new_tests_as_fixed(self) -> None:
        """Only test changes enter the parent; fixed code stays separate."""
        destination = self.root / "curator"
        receipt = prepare(self.case, destination)
        self.assertEqual((destination / "parent/module.txt").read_text(), "broken\n")
        self.assertEqual((destination / "fixed/module.txt").read_text(), "fixed\n")
        self.assertEqual(
            (destination / "parent/tests.txt").read_bytes(),
            (destination / "fixed/tests.txt").read_bytes(),
        )
        self.assertFalse(receipt["ready_for_model_comparison"])
        self.assertEqual(json.loads((destination / "preparation.json").read_text()), receipt)
        self.assertTrue((destination / "CURATOR_ONLY.txt").exists())

    def test_ambient_diff_settings_do_not_change_catalog_digest(self) -> None:
        """Preserve fixed patch identity despite global and environment diff settings."""
        config = self.root / "hostile.gitconfig"
        config.write_text(
            "[diff]\n noprefix = true\n mnemonicPrefix = true\n context = 0\n"
            " algorithm = histogram\n indentHeuristic = true\n renames = copies\n"
            " interHunkContext = 9\n external = false\n"
            "[core]\n abbrev = 12\n[color]\n ui = always\n"
        )
        destination = self.root / "hostile-curator"
        with patch.dict(
            os.environ,
            {
                "GIT_CONFIG_GLOBAL": str(config),
                "GIT_DIFF_OPTS": "--unified=0",
                "GIT_EXTERNAL_DIFF": "false",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "diff.noprefix",
                "GIT_CONFIG_VALUE_0": "true",
            },
        ):
            receipt = prepare(self.case, destination)
        self.assertEqual(receipt["test_patch_sha256"], self.case["test_patch_sha256"])
        self.assertEqual((destination / "parent/module.txt").read_text(), "broken\n")
        self.assertEqual((destination / "parent/tests.txt").read_text(), "new behavioral check\n")

    def test_occupied_destination_is_preserved(self) -> None:
        """Never reuse or remove an existing user workspace."""
        destination = self.root / "occupied"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            prepare(self.case, destination)
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(destination.iterdir()), [marker])

    def test_incorrect_parent_and_test_hash_fail_before_worktrees(self) -> None:
        """Reject mismatched provenance before exposing prepared controls."""
        for field in ("parent", "test_patch_sha256"):
            with self.subTest(field=field):
                case = dict(self.case)
                case[field] = "0" * (40 if field == "parent" else 64)
                destination = self.root / field
                with self.assertRaises(ValueError):
                    prepare(case, destination)
                self.assertFalse((destination / "parent").exists())
                self.assertFalse((destination / "preparation.json").exists())
                self.assertTrue((destination / "CURATOR_ONLY.txt").exists())

    def test_catalog_has_only_four_unready_pinned_cases(self) -> None:
        """Keep preparation metadata separate from an actor-ready claim."""
        catalog = json.loads(CATALOG.read_text())
        self.assertFalse(catalog["ready_for_model_comparison"])
        self.assertEqual(len(catalog["cases"]), 4)
        self.assertEqual(len({case["id"] for case in catalog["cases"]}), 4)
        for case in catalog["cases"]:
            self.assertFalse(case["ready_for_model_comparison"])
            self.assertRegex(case["parent"], r"^[0-9a-f]{40}$")
            self.assertRegex(case["fixed"], r"^[0-9a-f]{40}$")
            self.assertRegex(case["test_patch_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(case["task"])
            self.assertTrue(case["test_paths"])
