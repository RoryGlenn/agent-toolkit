"""Exercise selection migration and retirement through real disposable project installs."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import install
import project_bootstrap as project

ROOT = Path(__file__).resolve().parents[1]


class ProjectReconfigurationTests(unittest.TestCase):
    """Keep destructive selection changes explicit, ownership-bound and recoverable."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source = self.base / "toolkit"
        self.source.mkdir()
        for name in ("skills", "agents"):
            shutil.copytree(
                ROOT / name,
                self.source / name,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
            )
        for name in ("install.py", "project_bootstrap.py"):
            shutil.copyfile(ROOT / name, self.source / name)
        self.app = self.base / "application"

    def apply(self, **options: object) -> str:
        """Run the source API, returning its complete preflight plan."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            project.bootstrap(
                self.source,
                self.app,
                install.inventory(self.source),
                install.AGENTS,
                install.IGNORED,
                **options,
            )
        return output.getvalue()

    def cli(self, *options: str, success: bool = True) -> subprocess.CompletedProcess[str]:
        """Run the actual standalone CLI, including its parser and inventory validation."""
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.source / "install.py"),
                "bootstrap",
                "--project",
                str(self.app),
                *options,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def manifest(self) -> dict:
        return json.loads((self.app / project.MANIFEST).read_text())

    def legacy(self) -> None:
        """Use the published pre-routing v1 project, not a fabricated new-schema fixture."""
        shutil.copytree(ROOT / "tests/fixtures/pre-routing-project", self.app)

    def snapshot(self) -> dict:
        """Include identities and modes so a preview cannot silently replace a file."""
        return {
            str(p.relative_to(self.app)): (
                p.lstat().st_ino,
                p.lstat().st_mode,
                str(p.readlink()) if p.is_symlink() else p.read_bytes() if p.is_file() else None,
            )
            for p in self.app.rglob("*")
        }

    def contents(self) -> dict:
        """Rollback may atomically restore inodes; require original bytes and modes."""
        return {name: state[1:] for name, state in self.snapshot().items()}

    def test_new_roots_are_distinct_and_repeat_is_noop(self) -> None:
        self.cli("--skill", "ddia-design-skill", "--target", "codex")
        manifest = self.manifest()
        self.assertEqual(manifest["schema"], "agent-toolkit-project/v2")
        self.assertEqual(manifest["requested_skills"], ["ddia-design-skill"])
        self.assertEqual(
            manifest["skills"], ["ddia-design-skill", "ddia-skill", "task-routing-skill"]
        )
        before = self.snapshot()
        self.assertIn("no changes", self.cli().stdout)
        self.assertEqual(before, self.snapshot())
        self.cli("--check")

    def test_normal_modes_refuse_root_changes_even_with_same_closure(self) -> None:
        self.apply(skills=["ddia-design-skill"], target="codex")
        before = self.snapshot()
        for mode in ([], ["--update"]):
            result = self.cli(
                *mode, "--skill", "ddia-design-skill", "--skill", "ddia-skill", success=False
            )
            self.assertIn("--reconfigure", result.stderr)
            self.assertEqual(before, self.snapshot())

    def test_real_v1_update_preserves_unknown_root_intent(self) -> None:
        self.legacy()
        self.cli("--update")
        manifest = self.manifest()
        self.assertEqual(manifest["schema"], "agent-toolkit-project/v1")
        self.assertNotIn("requested_skills", manifest)
        self.assertEqual(manifest["skills"], ["release-and-docs-skill", "task-routing-skill"])
        before = self.snapshot()
        self.cli()
        self.cli("--check")
        self.assertEqual(before, self.snapshot())

    def test_legacy_migration_requires_complete_selection(self) -> None:
        self.legacy()
        before = self.snapshot()
        result = self.cli("--reconfigure", "--target", "codex", success=False)
        self.assertIn("complete", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.cli("--reconfigure", "--skill", "documentation-skill", "--target", "codex")
        manifest = self.manifest()
        self.assertEqual(manifest["requested_skills"], ["documentation-skill"])
        self.assertEqual(manifest["schema"], "agent-toolkit-project/v2")
        self.assertFalse((self.app / ".agents/skills/release-and-docs-skill/SKILL.md").exists())
        self.cli("--check")

    def test_obsolete_catalog_package_can_be_inspected_and_retired(self) -> None:
        self.cli("--skill", "simplify-or-delete-skill", "--target", "codex")
        shutil.rmtree(self.source / "skills/simplify-or-delete-skill")
        self.cli("--check")
        before = self.snapshot()
        self.assertIn("unavailable", self.cli("--update", success=False).stderr)
        self.assertEqual(before, self.snapshot())
        preview = self.cli("--reconfigure", "--skill", "documentation-skill", "--dry-run")
        self.assertIn("remove owned file", preview.stdout)
        self.assertEqual(before, self.snapshot())
        self.cli("--reconfigure", "--skill", "documentation-skill")
        self.assertFalse((self.app / ".agents/skills/simplify-or-delete-skill/SKILL.md").exists())
        self.cli("--check")

    def test_retirement_preserves_shared_roles_and_upstream_files(self) -> None:
        self.apply(
            skills=["issue-to-tested-pr-skill", "independent-diff-review-skill"], target="codex"
        )
        upstream = self.app / ".agents/skills/openspec-apply-change/SKILL.md"
        upstream.parent.mkdir()
        upstream.write_bytes(b"upstream-generated bytes\n")
        note = self.app / ".agents/skills/issue-to-tested-pr-skill/team-note.md"
        note.write_text("unowned team note")
        instructions = self.app / "AGENTS.md"
        instructions.write_bytes(b"team prefix\n" + instructions.read_bytes() + b"team suffix\n")
        self.apply(skills=["independent-diff-review-skill"], reconfigure=True)
        for name in ("adversarial-reviewer-agent.toml", "verifier-agent.toml"):
            self.assertTrue((self.app / ".codex/agents" / name).is_file())
        self.assertFalse((self.app / ".codex/agents/implementation-owner-agent.toml").exists())
        self.assertTrue((self.app / ".agents/skills/task-routing-skill/SKILL.md").is_file())
        self.assertEqual(upstream.read_bytes(), b"upstream-generated bytes\n")
        self.assertEqual(note.read_text(), "unowned team note")
        self.assertTrue(instructions.read_bytes().startswith(b"team prefix\n"))
        self.assertTrue(instructions.read_bytes().endswith(b"team suffix\n"))
        self.cli("--check")

    def test_v2_host_only_change_retains_roots_and_unowned_roles(self) -> None:
        self.cli("--skill", "documentation-skill", "--target", "codex")
        role = self.app / ".codex/agents/team-agent.toml"
        role.write_text("team owned")
        before = self.snapshot()
        preview = self.cli("--reconfigure", "--target", "copilot", "--dry-run")
        self.assertIn("documentation-agent.toml: remove owned file", preview.stdout)
        self.assertEqual(before, self.snapshot())
        self.cli("--reconfigure", "--target", "copilot")
        self.assertEqual(self.manifest()["requested_skills"], ["documentation-skill"])
        self.assertEqual(self.manifest()["hosts"], ["copilot"])
        self.assertFalse((self.app / ".codex/agents/documentation-agent.toml").exists())
        self.assertEqual(role.read_text(), "team owned")
        self.assertFalse((self.app / ".github/agents").exists())
        self.cli("--check")

    def test_ordinary_update_retains_no_longer_required_dependency(self) -> None:
        self.apply(skills=["ddia-design-skill"], target="codex")
        with patch.dict(project.SKILL_DEPENDENCIES, {"ddia-design-skill": ("task-routing-skill",)}):
            self.apply(update=True, skills=["ddia-design-skill"])
            self.assertIn("ddia-skill", self.manifest()["skills"])
            self.assertEqual(self.manifest()["requested_skills"], ["ddia-design-skill"])
            self.apply(reconfigure=True, target="codex")
            self.assertNotIn("ddia-skill", self.manifest()["skills"])
            self.assertFalse((self.app / ".agents/skills/ddia-skill/SKILL.md").exists())

    def test_refuses_edited_missing_and_linked_retired_content(self) -> None:
        self.apply(skills=["documentation-skill"], target="codex")
        owned = self.app / ".agents/skills/documentation-skill/SKILL.md"
        original = owned.read_bytes()
        for kind in ("edited", "missing", "link"):
            with self.subTest(kind=kind):
                owned.unlink()
                if kind == "edited":
                    owned.write_bytes(original + b"\nteam edit\n")
                elif kind == "link":
                    owned.symlink_to(self.source / "skills/documentation-skill/SKILL.md")
                before = self.snapshot()
                self.cli("--reconfigure", "--skill", "task-routing-skill", success=False)
                self.assertEqual(before, self.snapshot())
                if owned.is_symlink() or owned.exists():
                    owned.unlink()
                owned.write_bytes(original)

    def test_collision_and_block_edit_refuse_before_retirement(self) -> None:
        self.apply(skills=["task-routing-skill"], target="codex")
        collision = self.app / ".codex/agents/documentation-agent.toml"
        collision.parent.mkdir(parents=True)
        collision.write_text("unmanaged")
        before = self.snapshot()
        self.cli("--reconfigure", "--skill", "documentation-skill", success=False)
        self.assertEqual(before, self.snapshot())
        collision.unlink()
        instructions = self.app / "AGENTS.md"
        instructions.write_bytes(
            instructions.read_bytes().replace(b"Shared engineering", b"Edited")
        )
        before = self.snapshot()
        self.cli("--reconfigure", "--skill", "documentation-skill", success=False)
        self.assertEqual(before, self.snapshot())

    def test_late_failure_restores_additions_removals_modes_and_manifest(self) -> None:
        self.apply(skills=["documentation-skill"], target="codex")
        (self.app / ".agents/skills/documentation-skill/SKILL.md").chmod(0o600)
        before = self.contents()
        write = project.write_file

        def fail_manifest_once(path: Path, state: project.FileState) -> None:
            if path.name == "manifest.json":
                raise OSError("simulated late failure")
            write(path, state)

        with patch.object(project, "write_file", side_effect=fail_manifest_once):
            with self.assertRaisesRegex(project.BootstrapError, "rolled back"):
                self.apply(reconfigure=True, skills=["ddia-skill"], target="copilot")
        self.assertEqual(before, self.contents())
        self.cli("--check")

    def test_invalid_modes_and_absent_target_have_no_writes(self) -> None:
        for options in (
            ("--reconfigure", "--skill", "documentation-skill"),
            ("--reconfigure", "--update"),
            ("--check", "--reconfigure"),
        ):
            self.cli(*options, success=False)
            self.assertFalse(self.app.exists())
        self.apply(skills=["task-routing-skill"])
        before = self.snapshot()
        self.cli("--reconfigure", success=False)
        self.assertEqual(before, self.snapshot())

    def test_invalid_v2_roots_fail_integrity_and_reconfiguration(self) -> None:
        self.apply(skills=["documentation-skill"], target="codex")
        path = self.app / project.MANIFEST
        original = path.read_bytes()
        for value in (
            None,
            [],
            ["../escape-skill"],
            ["unknown-skill"],
            ["documentation-skill", "documentation-skill"],
            "documentation-skill",
        ):
            with self.subTest(value=value):
                manifest = json.loads(original)
                if value is None:
                    manifest.pop("requested_skills")
                else:
                    manifest["requested_skills"] = value
                path.write_text(json.dumps(manifest))
                before = self.snapshot()
                self.cli("--check", success=False)
                self.cli("--reconfigure", "--skill", "task-routing-skill", success=False)
                self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
