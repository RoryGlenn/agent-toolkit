"""Behavior checks for non-destructive package discovery and installation."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> ModuleType:
    """Load a package script for direct, isolated behavior tests.

    Parameters
    ----------
    name : str
        Unique module name.
    path : Path
        Python script to load.

    Returns
    -------
    ModuleType
        Imported script module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_module("doctor", ROOT / "skills/doc-agent/scripts/check_environment.py")


class DiscoveryTests(unittest.TestCase):
    """Check bounded, non-executing project inspection."""

    def setUp(self) -> None:
        """Make an isolated project for every test."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_commands_are_listed_without_executing_or_printing_bodies(self) -> None:
        """Only a safe script invocation is reported, never its arbitrary body."""
        sentinel = self.root / "MUST_NOT_EXIST"
        manifest = self.root / "package.json"
        manifest.write_text(
            json.dumps(
                {
                    "packageManager": "pnpm@10.0.0",
                    "scripts": {
                        "docs:build": f"touch {sentinel}; echo PRIVATE_TOKEN",
                        "start": "other",
                    },
                }
            )
        )
        before = manifest.read_bytes()
        report = doctor.inspect_project(self.root)
        self.assertFalse(sentinel.exists())
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(report["commands"][0]["argv"], ["pnpm", "run", "docs:build"])
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(report))

    def test_malformed_manifest_is_reported(self) -> None:
        """Bad JSON is a limitation, not a traceback or inferred command."""
        (self.root / "package.json").write_text("{invalid")
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"], [])
        self.assertTrue(report["warnings"])

    def test_wrong_manifest_shapes_are_reported(self) -> None:
        """Unexpected JSON types cannot crash command discovery."""
        for value in ([], {"scripts": []}, {"scripts": {"docs": None}}):
            with self.subTest(value=value):
                (self.root / "package.json").write_text(json.dumps(value))
                self.assertEqual(doctor.inspect_project(self.root)["commands"], [])

    def test_excluded_and_deep_directories_are_not_scanned(self) -> None:
        """Dependency caches and excessive depth do not inflate the inventory."""
        for name in ("node_modules/pkg", ".git/sub", "a/b/c/d"):
            folder = self.root / name
            folder.mkdir(parents=True)
            (folder / "package.json").write_text('{"scripts":{"docs":"anything"}}')
        self.assertEqual(doctor.inspect_project(self.root)["configs"], [])

    def test_linked_configuration_is_not_read(self) -> None:
        """A manifest symlink is identified and not parsed."""
        outside = self.root / "private.txt"
        outside.write_text('{"scripts":{"docs":"SECRET"}}')
        (self.root / "package.json").symlink_to(outside)
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"], [])
        self.assertIn("Skipped symlink", report["warnings"][0])

    def test_missing_optional_tools_do_not_fail(self) -> None:
        """Documentation work is still possible without optional validators."""
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.inspect_project(self.root)
        self.assertTrue(all(value is None for value in report["tools"].values()))

    def test_workspace_inherits_ancestor_package_manager(self) -> None:
        """A nested package uses the selected workspace's declared manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "packages/docs"
        child.mkdir(parents=True)
        (child / "package.json").write_text('{"scripts":{"docs:build":"build"}}')
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"][0]["argv"], ["yarn", "run", "docs:build"])

    def test_workspace_inherits_lockfile(self) -> None:
        """Lockfile evidence is inherited when no declaration exists."""
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: 9")
        child = self.root / "docs"
        child.mkdir()
        (child / "package.json").write_text('{"scripts":{"build":"build"}}')
        self.assertEqual(doctor.inspect_project(self.root)["commands"][0]["argv"][0], "pnpm")

    def test_nearest_declaration_wins(self) -> None:
        """An explicitly configured nested project keeps its own manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "docs"
        child.mkdir()
        (child / "package.json").write_text(
            '{"packageManager":"bun@1.0.0","scripts":{"build":"build"}}'
        )
        self.assertEqual(doctor.inspect_project(self.root)["commands"][0]["argv"][0], "bun")

    def test_manager_discovery_stays_inside_explicit_root(self) -> None:
        """An unrelated parent manifest is not used to guess a manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "selected-project"
        child.mkdir()
        (child / "package.json").write_text('{"scripts":{"build":"build"}}')
        self.assertIsNone(doctor.inspect_project(child)["commands"][0]["argv"])

    def test_conflicting_lockfiles_do_not_guess_manager(self) -> None:
        """Conflicting evidence is reported instead of choosing a tool arbitrarily."""
        (self.root / "yarn.lock").write_text("")
        (self.root / "package-lock.json").write_text("{}")
        (self.root / "package.json").write_text('{"scripts":{"build":"build"}}')
        command = doctor.inspect_project(self.root)["commands"][0]
        self.assertIsNone(command["argv"])
        self.assertIn("conflicting", command["package_manager_evidence"])

    def test_invalid_project_is_rejected(self) -> None:
        """A missing root returns a meaningful input error."""
        with self.assertRaises(ValueError):
            doctor.inspect_project(self.root / "missing")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named pipes require POSIX mkfifo")
    def test_fifo_manifest_returns_without_blocking(self) -> None:
        """A real FIFO is skipped, with a subprocess timeout bounding regressions."""
        os.mkfifo(self.root / "package.json")
        checker = ROOT / "skills/doc-agent/scripts/check_environment.py"
        result = subprocess.run(
            [sys.executable, "-B", str(checker), "--project", str(self.root), "--json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["commands"], [])
        self.assertIn("Skipped non-regular manifest: package.json", report["warnings"])


if __name__ == "__main__":
    unittest.main()
