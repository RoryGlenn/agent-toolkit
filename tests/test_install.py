"""Exercise the installer against disposable host directories and real package files."""

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import install

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    """Verify installation and recovery without touching a real user home."""

    def setUp(self) -> None:
        """Create isolated sources and destinations, including spaces in paths."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "source toolkit"
        self.root.mkdir()
        for name in ("skills", "agents"):
            shutil.copytree(
                ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
            )
        self.home = self.base / "test home"
        self.codex = self.home / ".codex"
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def apply(
        self,
        skills: list[str] | None = None,
        *,
        target: str = "codex",
        backup_existing: bool = False,
        dry_run: bool = False,
    ) -> Path | None:
        """Install a selected package into this test's isolated home."""
        return install.install(
            self.root,
            target,
            skills or ["doc-agent"],
            self.home,
            self.codex,
            backup_existing=backup_existing,
            dry_run=dry_run,
        )

    def test_selected_install_links_canonical_skill_and_agent(self) -> None:
        """A selected docs install exposes the complete skill and its wrapper."""
        receipt = self.apply()
        self.assertIsNotNone(receipt)
        skill = self.home / ".agents/skills/doc-agent"
        self.assertEqual(skill.resolve(), self.root / "skills/doc-agent")
        self.assertTrue((skill / "references/book-foundation.md").is_file())
        role = self.codex / "agents/doc-agent.toml"
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(self.root / "agents/codex/doc-agent.toml"))
        with os.fdopen(os.open(role, os.O_RDONLY | os.O_NOFOLLOW)) as handle:
            self.assertIn('name = "doc_agent"', handle.read())
        self.assertFalse((self.home / ".agents/skills/recruiter-followup").exists())
        (self.root / "skills/doc-agent/local-example.md").write_text("new content")
        self.assertEqual((skill / "local-example.md").read_text(), "new content")

    def test_all_skills_and_associated_agents_for_both_hosts(self) -> None:
        """Each host receives all nine skills and only its supported wrappers."""
        skills = list(install.inventory(self.root))
        self.apply(skills)
        self.apply(skills, target="copilot")
        self.assertEqual(len(list((self.home / ".agents/skills").iterdir())), 9)
        self.assertEqual(len(list((self.codex / "agents").iterdir())), 6)
        self.assertEqual(len(list((self.home / ".copilot/skills").iterdir())), 9)
        self.assertEqual(len(list((self.home / ".copilot/agents").iterdir())), 1)

    def test_book_workflow_install_preserves_roles_and_restores_independently(self) -> None:
        """The coordinating skill installs alone without changing existing specialists."""
        self.apply(["ddia-specialist", "software-design-specialist"])
        roles = {
            path.name: (path.stat().st_ino, path.read_bytes())
            for path in (self.codex / "agents").iterdir()
        }
        receipt = self.apply(["book-to-agent"])
        assert receipt is not None
        skill = self.home / ".agents/skills/book-to-agent"
        self.assertEqual(skill.resolve(), self.root / "skills/book-to-agent")
        self.assertIsNone(self.apply(["book-to-agent"]))
        self.assertEqual(
            {
                path.name: (path.stat().st_ino, path.read_bytes())
                for path in (self.codex / "agents").iterdir()
            },
            roles,
        )
        install.restore(receipt)
        self.assertFalse(install.present(skill))
        self.assertTrue((self.home / ".agents/skills/ddia-specialist").is_symlink())
        self.assertTrue((self.home / ".agents/skills/software-design-specialist").is_symlink())
        self.assertEqual(
            {
                path.name: (path.stat().st_ino, path.read_bytes())
                for path in (self.codex / "agents").iterdir()
            },
            roles,
        )

    def test_legacy_role_symlink_migration_is_selected_and_reversible(self) -> None:
        """Selected roles become regular files; old receipts and symlink backups still restore."""
        original_receipt = self.apply()
        assert original_receipt is not None
        role = self.codex / "agents/doc-agent.toml"
        source = self.root / "agents/codex/doc-agent.toml"
        role.unlink()
        role.symlink_to(source)  # Simulate a role installed by the original v1 installer.
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        receipt = self.apply(backup_existing=True)
        assert receipt is not None
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(source))
        install.restore(receipt)
        self.assertTrue(role.is_symlink())
        with patch.object(install, "write_receipt", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                install.restore(original_receipt)
        self.assertTrue(role.is_symlink())
        install.restore(original_receipt)
        self.assertFalse(install.present(role))

    def test_atomic_role_replacement_requires_preserving_reinstall(self) -> None:
        """A source inode replacement cannot silently leave an outdated role marked current."""
        receipt = self.apply()
        assert receipt is not None
        source = self.root / "agents/codex/doc-agent.toml"
        role = self.codex / "agents/doc-agent.toml"
        old = role.read_text()
        replacement = source.with_suffix(".new")
        replacement.write_text(old + "\n# New version\n")
        replacement.replace(source)
        self.assertEqual(role.read_text(), old)
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        with self.assertRaisesRegex(install.InstallError, "has changed"):
            install.restore(receipt)
        refreshed = self.apply(backup_existing=True)
        assert refreshed is not None
        self.assertTrue(role.samefile(source))
        install.restore(refreshed)
        self.assertEqual(role.read_text(), old)

    def test_cross_device_role_link_failure_rolls_back(self) -> None:
        """An unsupported cross-volume hard link leaves no partial installation."""
        with patch.object(os, "link", side_effect=OSError(errno.EXDEV, "Cross-device link")):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                self.apply()
        self.assertFalse(self.home.exists())

    def test_repeat_install_is_a_noop(self) -> None:
        """Repeated installs preserve existing links and do not add receipts."""
        receipt = self.apply()
        assert receipt is not None
        installed = self.home / ".agents/skills/doc-agent"
        before = installed.lstat()
        self.assertIsNone(self.apply())
        self.assertEqual(installed.lstat().st_ino, before.st_ino)
        self.assertEqual(len(list(receipt.parent.parent.iterdir())), 1)

    def test_dry_run_does_not_create_home(self) -> None:
        """Preview is read-only even when no destination directories exist."""
        self.apply(dry_run=True)
        self.assertFalse(self.home.exists())

    def test_conflict_aborts_all_changes(self) -> None:
        """A late agent conflict cannot leave an earlier skill installed."""
        conflict = self.codex / "agents/doc-agent.toml"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("local instructions")
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        self.assertEqual(conflict.read_text(), "local instructions")
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".local").exists())

    def test_backup_restore_roundtrip_preserves_directory_file_and_broken_link(self) -> None:
        """Migration retains different destination types and unrelated settings."""
        skill = self.home / ".agents/skills/doc-agent"
        skill.mkdir(parents=True)
        (skill / "custom.md").write_text("custom skill")
        agent = self.codex / "agents/doc-agent.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text("custom agent")
        legacy = self.codex / "skills/doc-agent"
        legacy.parent.mkdir()
        legacy.symlink_to("../missing-old-source")
        config = self.codex / "config.toml"
        config.write_text("preserve settings")
        receipt = self.apply(backup_existing=True)
        assert receipt is not None
        self.assertFalse(install.present(legacy))
        self.assertTrue(skill.is_symlink())
        install.restore(receipt, dry_run=True)
        self.assertTrue(skill.is_symlink())
        install.restore(receipt)
        self.assertFalse(skill.is_symlink())
        self.assertEqual((skill / "custom.md").read_text(), "custom skill")
        self.assertEqual(agent.read_text(), "custom agent")
        self.assertEqual(os.readlink(legacy), "../missing-old-source")
        self.assertEqual(config.read_text(), "preserve settings")
        self.assertEqual(json.loads(receipt.read_text())["state"], "restored")

    def test_legacy_copy_requires_explicit_backup(self) -> None:
        """Installing a new location cannot silently leave an older duplicate active."""
        legacy = self.codex / "skills/doc-agent"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("old")
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        self.assertFalse((self.home / ".agents").exists())

    def test_broken_destination_link_conflicts(self) -> None:
        """Dangling links are treated as user content, not empty destinations."""
        destination = self.home / ".agents/skills/doc-agent"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(self.base / "missing")
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertTrue(destination.is_symlink())

    def test_source_symlink_is_rejected_before_writes(self) -> None:
        """An internal source link never exposes unrelated files to the host."""
        (self.root / "skills/doc-agent/private").symlink_to(self.base / "missing")
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_source_root_symlink_is_rejected_before_writes(self) -> None:
        """A symlink replacing the skills directory cannot bypass validation."""
        (self.root / "skills").rename(self.base / "external-skills")
        (self.root / "skills").symlink_to(self.base / "external-skills")
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertFalse(self.home.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named pipes require POSIX")
    def test_special_source_file_is_rejected_without_reading(self) -> None:
        """Named pipes fail validation rather than blocking on a read."""
        os.mkfifo(self.root / "skills/doc-agent/pipe")
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_source_scan_error_aborts_before_writes(self) -> None:
        """A failed scan cannot silently omit package resources."""
        scan = os.scandir

        def fail(path: Path) -> os.ScandirIterator[str]:
            if Path(path).name == "references":
                raise PermissionError("simulated unreadable references")
            return scan(path)

        with patch.object(install.os, "scandir", side_effect=fail):
            with self.assertRaises(PermissionError):
                self.apply()
        self.assertFalse(self.home.exists())

    def test_destination_parent_symlink_is_rejected(self) -> None:
        """Parent links cannot redirect host writes to another directory."""
        self.home.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.home / ".agents").symlink_to(outside)
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertEqual(list(outside.iterdir()), [])

    def test_unknown_skill_and_invalid_metadata_fail_before_writes(self) -> None:
        """Selection mistakes and malformed packages fail without partial installs."""
        with self.assertRaisesRegex(install.InstallError, "Unknown skills"):
            self.apply(["missing-skill"])
        (self.root / "skills/doc-agent/SKILL.md").write_text("missing metadata")
        with self.assertRaisesRegex(install.InstallError, "frontmatter"):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_late_link_failure_rolls_back_backups_and_new_directories(self) -> None:
        """An ordinary write failure restores all earlier user entries."""
        legacy = self.codex / "skills/doc-agent"
        legacy.mkdir(parents=True)
        (legacy / "custom.md").write_text("preserve")
        with patch.object(os, "link", side_effect=OSError("simulated full disk")):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                self.apply(backup_existing=True)
        self.assertEqual((legacy / "custom.md").read_text(), "preserve")
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".local").exists())
        self.assertFalse((self.codex / "agents").exists())

    def test_final_receipt_failure_restores_moved_legacy_entry(self) -> None:
        """Failure persisting the final receipt restores moved backups as well."""
        legacy = self.codex / "skills/doc-agent"
        legacy.mkdir(parents=True)
        (legacy / "custom.md").write_text("preserve")
        write = install.write_receipt

        def fail(path: Path, data: dict[str, object]) -> None:
            if data["state"] == "installed":
                raise OSError("simulated receipt failure")
            write(path, data)

        with patch.object(install, "write_receipt", side_effect=fail):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                self.apply(backup_existing=True)
        self.assertEqual((legacy / "custom.md").read_text(), "preserve")
        self.assertFalse((self.home / ".agents").exists())

    def test_restore_refuses_changed_destination_before_any_changes(self) -> None:
        """Restoration never removes a destination replaced after installation."""
        receipt = self.apply()
        assert receipt is not None
        agent = self.codex / "agents/doc-agent.toml"
        agent.unlink()
        agent.write_text("new local work")
        with self.assertRaisesRegex(install.InstallError, "has changed"):
            install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/doc-agent").is_symlink())
        self.assertEqual(agent.read_text(), "new local work")

    def test_restore_refuses_missing_backup_before_any_changes(self) -> None:
        """An incomplete backup cannot cause partial restoration."""
        legacy = self.codex / "skills/doc-agent"
        legacy.mkdir(parents=True)
        receipt = self.apply(backup_existing=True)
        assert receipt is not None
        (receipt.parent / "2").rmdir()
        with self.assertRaisesRegex(install.InstallError, "backup is missing"):
            install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/doc-agent").is_symlink())

    def test_restore_failure_reinstates_installed_links(self) -> None:
        """An ordinary restoration failure leaves the completed install usable."""
        receipt = self.apply()
        assert receipt is not None
        with patch.object(install, "write_receipt", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/doc-agent").is_symlink())
        self.assertTrue(
            (self.codex / "agents/doc-agent.toml").samefile(
                self.root / "agents/codex/doc-agent.toml"
            )
        )
        self.assertFalse((self.codex / "agents/doc-agent.toml").is_symlink())
        self.assertEqual(json.loads(receipt.read_text())["state"], "installed")

    def test_restore_fresh_install_removes_only_toolkit_links(self) -> None:
        """Restoring a fresh install preserves unrelated host files."""
        receipt = self.apply()
        assert receipt is not None
        unrelated = self.codex / "config.toml"
        unrelated.write_text("keep")
        install.restore(receipt)
        self.assertFalse(install.present(self.home / ".agents/skills/doc-agent"))
        self.assertFalse(install.present(self.codex / "agents/doc-agent.toml"))
        self.assertEqual(unrelated.read_text(), "keep")

    def test_custom_codex_home(self) -> None:
        """A custom Codex home changes agent and legacy paths, not shared skills."""
        self.codex = self.base / "custom codex"
        self.apply()
        self.assertTrue(
            (self.codex / "agents/doc-agent.toml").samefile(
                self.root / "agents/codex/doc-agent.toml"
            )
        )
        self.assertTrue((self.home / ".agents/skills/doc-agent").is_symlink())
        self.assertFalse((self.home / ".codex").exists())

    def test_codex_home_cannot_retire_canonical_source(self) -> None:
        """A Codex home equal to the checkout cannot move its source skills."""
        self.codex = self.root
        skill = self.root / "skills/doc-agent/SKILL.md"
        before = skill.read_bytes()
        with self.assertRaisesRegex(install.InstallError, "overlap"):
            self.apply(backup_existing=True)
        self.assertEqual(skill.read_bytes(), before)
        self.assertFalse((self.root / "skills/doc-agent").is_symlink())
        self.assertFalse(self.home.exists())

    def test_aliasing_legacy_location_cannot_remove_installed_skill(self) -> None:
        """A repeat install cannot mistake its active skill for a legacy copy."""
        self.apply()
        skill = self.home / ".agents/skills/doc-agent"
        before = skill.lstat()
        receipts = list((self.home / ".local/state/agent-toolkit/installations").iterdir())
        self.codex = self.home / ".agents"
        with self.assertRaisesRegex(install.InstallError, "overlap"):
            self.apply(backup_existing=True)
        self.assertEqual(skill.lstat().st_ino, before.st_ino)
        self.assertEqual(skill.resolve(), self.root / "skills/doc-agent")
        self.assertEqual(
            list((self.home / ".local/state/agent-toolkit/installations").iterdir()), receipts
        )
        self.assertFalse((self.home / ".agents/agents").exists())

    def test_nested_destination_and_backup_roots_are_rejected(self) -> None:
        """Host roots and backup storage cannot contain one another."""
        for codex_home in (
            self.home / ".agents/skills",
            self.home / ".local/state/agent-toolkit/installations",
            self.home / ".agents/../.agents",
        ):
            with self.subTest(codex_home=codex_home):
                self.codex = codex_home
                with self.assertRaisesRegex(install.InstallError, "overlap"):
                    self.apply(backup_existing=True)
                self.assertFalse(self.home.exists())

    def test_disposable_home_inside_checkout_is_rejected(self) -> None:
        """Generated host files and backups cannot enter the canonical checkout."""
        self.home = self.root / "disposable home"
        self.codex = self.home / ".codex"
        with self.assertRaisesRegex(install.InstallError, "overlap"):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_selected_review_installs_its_required_roles(self) -> None:
        """A review-only selection supplies both independent Codex roles."""
        self.apply(["independent-diff-review"])
        self.assertEqual(
            sorted(path.name for path in (self.codex / "agents").iterdir()),
            ["adversarial-reviewer.toml", "verifier.toml"],
        )
        self.assertFalse((self.home / ".agents/skills/issue-to-tested-pr").exists())

    def test_shared_agent_dependencies_are_installed_once(self) -> None:
        """Combined workflow selections produce one receipt entry per destination."""
        selected = ["independent-diff-review", "issue-to-tested-pr"]
        receipt = self.apply(selected)
        assert receipt is not None
        entries = json.loads(receipt.read_text())["entries"]
        destinations = [(entry["area"], entry["name"]) for entry in entries]
        self.assertEqual(len(destinations), 5)
        self.assertEqual(len(destinations), len(set(destinations)))
        self.assertIsNone(self.apply(selected))
        install.restore(receipt)
        self.assertEqual(list((self.codex / "agents").iterdir()), [])

    def test_explicit_cli_home_ignores_inherited_codex_home(self) -> None:
        """A disposable CLI install cannot accidentally use the caller's Codex home."""
        outside = self.base / "inherited codex"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "install.py"),
                "install",
                "--target",
                "codex",
                "--skill",
                "doc-agent",
                "--home",
                str(self.home),
            ],
            env={**os.environ, "CODEX_HOME": str(outside)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (self.codex / "agents/doc-agent.toml").samefile(ROOT / "agents/codex/doc-agent.toml")
        )
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
