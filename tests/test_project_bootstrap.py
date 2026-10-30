"""Exercise portable project copies, ownership, updates, and recovery in temporary repositories."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import install
import project_bootstrap as project

ROOT = Path(__file__).resolve().parents[1]


class ProjectBootstrapTests(unittest.TestCase):
    """Validate actual generated projects without altering personal host configuration."""

    def setUp(self) -> None:
        """Build an isolated source archive and an application destination."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source = self.base / "toolkit source"
        self.source.mkdir()
        for name in ("skills", "agents"):
            shutil.copytree(
                ROOT / name,
                self.source / name,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
            )
        for name in ("install.py", "project_bootstrap.py"):
            shutil.copyfile(ROOT / name, self.source / name)
        self.app = self.base / "new application"
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def apply(self, **options: object) -> None:
        """Bootstrap the isolated application with the validated source inventory."""
        project.bootstrap(
            self.source,
            self.app,
            install.inventory(self.source),
            install.AGENTS,
            install.IGNORED,
            **options,
        )

    def manifest(self) -> dict[str, object]:
        """Read generated ownership and provenance as a collaborator would."""
        return json.loads((self.app / project.MANIFEST).read_bytes())

    def snapshot(self) -> dict[str, tuple[int, int, bytes | str | None]]:
        """Capture application entries, identities, modes, and bytes for no-write assertions."""
        if not self.app.exists():
            return {}
        return {
            path.relative_to(self.app).as_posix(): (
                path.lstat().st_ino,
                path.lstat().st_mode,
                str(path.readlink())
                if path.is_symlink()
                else path.read_bytes()
                if path.is_file()
                else None,
            )
            for path in self.app.rglob("*")
        }

    def test_default_profile_is_portable_engineering_for_both_hosts(self) -> None:
        """A fresh project gets engineering guidance and host roles, without private material."""
        self.apply()
        self.assertEqual(
            {path.name for path in (self.app / ".agents/skills").iterdir()},
            {
                "documentation-skill",
                "ddia-skill",
                "software-design-skill",
                "independent-diff-review-skill",
                "issue-to-tested-pr-skill",
                "release-and-docs-skill",
                "simplify-or-delete-skill",
                "task-routing-skill",
            },
        )
        self.assertEqual(len(list((self.app / ".codex/agents").iterdir())), 6)
        self.assertFalse((self.app / ".github/agents").exists())
        self.assertFalse((self.app / "books").exists())
        self.assertFalse(list(self.app.rglob("*.epub")))
        for path in self.app.rglob("*"):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                self.assertEqual(path.stat().st_nlink, 1)
        instructions = (self.app / "AGENTS.md").read_text()
        self.assertIn(".agents/skills/issue-to-tested-pr-skill/SKILL.md", instructions)
        self.assertNotIn("ddia-assess-skill", instructions)
        self.assertNotIn("Toolkit contributions", instructions)
        manifest = self.manifest()
        self.assertEqual(manifest["hosts"], ["codex", "copilot"])
        serialized = json.dumps(manifest)
        self.assertNotIn(str(self.source), serialized)
        self.assertNotIn(str(self.app), serialized)
        self.assertNotIn(str(Path.home()), serialized)
        self.assertIsNone(manifest["source"]["commit"])
        self.assertIsNone(manifest["source"]["dirty"])
        self.assertEqual(len(manifest["source"]["content_sha256"]), 64)

    def test_role_rendering_inherits_settings_and_preserves_all_other_fields(self) -> None:
        """Copied Codex roles preserve instructions but inherit the collaborator's host settings."""
        self.apply()
        for path in (self.app / ".codex/agents").iterdir():
            original = tomllib.loads((self.source / "agents/codex" / path.name).read_text())
            rendered = tomllib.loads(path.read_text())
            self.assertEqual(
                rendered,
                {
                    key: value
                    for key, value in original.items()
                    if key not in {"model", "model_reasoning_effort", "sandbox_mode"}
                },
            )
        self.assertIn(
            'model = "gpt-5.6"',
            (self.source / "agents/codex/implementation-owner-agent.toml").read_text(),
        )
        wrapper = (self.app / ".codex/agents/documentation-agent.toml").read_text()
        self.assertIn(".agents/skills/documentation-skill/SKILL.md under that root", wrapper)

    def test_selected_copilot_profile_and_persisted_selection(self) -> None:
        """Explicit selection creates only its wrappers and becomes the repeat-command default."""
        self.apply(skills=["documentation-skill"], target="copilot")
        self.assertFalse((self.app / ".codex").exists())
        self.assertEqual(len(list((self.app / ".agents/skills").iterdir())), 2)
        instructions = (self.app / "AGENTS.md").read_text()
        self.assertNotIn("ddia-skill", instructions)
        before = self.snapshot()
        self.apply()
        self.assertEqual(self.snapshot(), before)
        with self.assertRaisesRegex(project.BootstrapError, "Changing project skills or hosts"):
            self.apply(target="both", update=True)
        self.assertEqual(self.snapshot(), before)

    def test_explicit_skill_only_selection_and_cli_defaults(self) -> None:
        """An explicit skill-only CLI selection creates its routes without host wrappers."""
        result = subprocess.run(
            [
                sys.executable,
                str(self.source / "install.py"),
                "bootstrap",
                "--project",
                str(self.app),
                "--skill",
                "release-and-docs-skill",
                "--skill",
                "simplify-or-delete-skill",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.app / ".codex").exists())
        self.assertFalse((self.app / ".github").exists())
        self.assertEqual(
            self.manifest()["skills"],
            ["release-and-docs-skill", "simplify-or-delete-skill", "task-routing-skill"],
        )
        self.assertIn("release-and-docs-skill", (self.app / "AGENTS.md").read_text())

    def test_relocated_project_runs_its_helper_after_source_removal(self) -> None:
        """A project clone/copy can use its files without the toolkit checkout or original path."""
        executable = self.source / "skills/documentation-skill/scripts/portable_probe.py"
        executable.write_text("#!/usr/bin/env python3\nprint('portable helper')\n")
        executable.chmod(0o755)
        self.apply(skills=["documentation-skill"])
        moved = self.base / "relocated application"
        self.app.rename(moved)
        shutil.rmtree(self.source)
        nested = moved / "src/nested"
        nested.mkdir(parents=True)
        result = subprocess.run(
            [
                sys.executable,
                str(moved / ".agents/skills/documentation-skill/scripts/check_environment.py"),
                "--project",
                str(moved),
                "--json",
            ],
            cwd=nested,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsInstance(json.loads(result.stdout), dict)
        copied_executable = moved / ".agents/skills/documentation-skill/scripts/portable_probe.py"
        self.assertEqual(copied_executable.stat().st_mode & 0o111, 0o111)
        executed = subprocess.run(
            [str(copied_executable)], cwd=nested, capture_output=True, text=True
        )
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(executed.stdout, "portable helper\n")
        self.assertFalse((moved / ".github/agents").exists())
        self.assertNotIn(str(self.source), (moved / project.MANIFEST).read_text())

    def test_dry_run_absent_target_and_unchanged_repeat_have_no_writes(self) -> None:
        """Planning creates no target; repeat installation preserves file identities."""
        self.apply(dry_run=True)
        self.assertFalse(self.app.exists())
        self.apply()
        before = self.snapshot()
        self.apply()
        self.apply(dry_run=True)
        self.assertEqual(self.snapshot(), before)

    def test_cli_dry_run_does_not_create_source_bytecode_or_project(self) -> None:
        """A first dry run from an unpacked source archive remains read-only."""
        before = {path.relative_to(self.source) for path in self.source.rglob("*")}
        result = subprocess.run(
            [
                sys.executable,
                str(self.source / "install.py"),
                "bootstrap",
                "--project",
                str(self.app),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.app.exists())
        self.assertEqual({path.relative_to(self.source) for path in self.source.rglob("*")}, before)

    def test_existing_project_instructions_preserved_across_update(self) -> None:
        """Only the owned block changes; outside bytes and unrelated project files survive."""
        self.app.mkdir()
        original = b"# Existing project\r\n\r\nUse the existing stack.\r\n"
        instructions = self.app / "AGENTS.md"
        instructions.write_bytes(original)
        (self.app / "app.py").write_text("print('application')\n")
        self.apply(skills=["documentation-skill"])
        self.assertTrue(instructions.read_bytes().startswith(original))
        instructions.write_bytes(
            b"added before\n" + instructions.read_bytes() + b"\nadded after\r\n"
        )
        unrelated = self.app / ".agents/skills/documentation-skill/project-note.md"
        unrelated.write_text("team-owned example")
        current = instructions.read_bytes()
        source_file = self.source / "skills/documentation-skill/assets/project-context.template.md"
        source_file.write_text(source_file.read_text() + "\nNew source guidance.\n")
        with self.assertRaisesRegex(project.BootstrapError, "--update --dry-run"):
            self.apply()
        before = self.snapshot()
        self.apply(update=True, dry_run=True)
        self.assertEqual(self.snapshot(), before)
        self.apply(update=True)
        self.assertEqual(instructions.read_bytes(), current)
        self.assertEqual(unrelated.read_text(), "team-owned example")
        self.assertEqual((self.app / "app.py").read_text(), "print('application')\n")
        self.assertIn(
            "New source guidance.",
            (
                self.app / ".agents/skills/documentation-skill/assets/project-context.template.md"
            ).read_text(),
        )

    def test_unmanaged_collision_aborts_the_entire_plan(self) -> None:
        """Even identical preexisting files require ownership rather than silent adoption."""
        path = self.app / ".codex/agents/verifier-agent.toml"
        path.parent.mkdir(parents=True)
        path.write_text("user's own role")
        before = self.snapshot()
        with self.assertRaisesRegex(project.BootstrapError, "Unmanaged destination"):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_local_file_or_managed_block_edits_refuse_update(self) -> None:
        """An update never overwrites locally customized managed content."""
        self.apply(skills=["documentation-skill"])
        path = self.app / ".agents/skills/documentation-skill/SKILL.md"
        original = path.read_bytes()
        path.write_bytes(original + b"\nTeam customization.\n")
        before = self.snapshot()
        with self.assertRaisesRegex(project.BootstrapError, "Managed file was edited"):
            self.apply(update=True)
        self.assertEqual(self.snapshot(), before)
        path.unlink()
        before = self.snapshot()
        with self.assertRaisesRegex(project.BootstrapError, "Managed file was edited or removed"):
            self.apply(update=True)
        self.assertEqual(self.snapshot(), before)
        path.write_bytes(original)
        instructions = self.app / "AGENTS.md"
        instructions.write_bytes(
            instructions.read_bytes().replace(b"Shared engineering", b"Edited engineering")
        )
        before = self.snapshot()
        with self.assertRaisesRegex(project.BootstrapError, "Managed AGENTS.md block was edited"):
            self.apply(update=True)
        self.assertEqual(self.snapshot(), before)

    def test_new_source_file_collision_and_removed_owned_file(self) -> None:
        """Updates add/remove owned source files while preserving unowned neighboring files."""
        self.apply(skills=["documentation-skill"])
        source = self.source / "skills/documentation-skill/assets/new.md"
        source.write_text("new toolkit asset")
        target = self.app / ".agents/skills/documentation-skill/assets/new.md"
        target.write_text("project-authored asset")
        before = self.snapshot()
        with self.assertRaisesRegex(project.BootstrapError, "Unmanaged destination"):
            self.apply(update=True)
        self.assertEqual(self.snapshot(), before)
        target.unlink()
        removed_source = self.source / "skills/documentation-skill/assets/example-check.template.md"
        removed_source.unlink()
        self.apply(update=True)
        self.assertEqual(target.read_text(), "new toolkit asset")
        self.assertFalse(
            (
                self.app / ".agents/skills/documentation-skill/assets/example-check.template.md"
            ).exists()
        )

    def test_initial_write_failure_rolls_back_created_files_and_directories(self) -> None:
        """A failure writing the last ownership record leaves no half-created project."""
        write = project.write_file

        def fail(path: Path, state: project.FileState) -> None:
            if path.name == "manifest.json":
                raise OSError("simulated manifest failure")
            write(path, state)

        with patch.object(project, "write_file", side_effect=fail):
            with self.assertRaisesRegex(project.BootstrapError, "rolled back"):
                self.apply()
        self.assertFalse(self.app.exists())

    def test_removed_owned_agents_update_without_touching_unrelated_roles(self) -> None:
        """Old ownership remains valid when the new source removes an associated role."""
        for host, extension in (("codex", ".toml"),):
            with self.subTest(host=host):
                self.app = self.base / f"removed-role-{host}"
                self.apply(skills=["documentation-skill"], target=host)
                directory = self.app / project.HOST_DIRECTORIES[host]
                owned = directory / f"documentation-agent{extension}"
                unrelated = directory / f"team-owned-agent{extension}"
                unrelated.write_text("preserve the team's own role")
                source = self.source / "agents" / host / owned.name
                original = source.read_bytes()
                source.unlink()
                try:
                    with patch.dict(install.AGENTS[host], {"documentation-skill": []}):
                        owned.write_bytes(owned.read_bytes() + b"\nLocal customization.\n")
                        before = self.snapshot()
                        with self.assertRaisesRegex(
                            project.BootstrapError, "Managed file was edited"
                        ):
                            self.apply(update=True)
                        self.assertEqual(self.snapshot(), before)
                        owned.write_bytes(
                            project.render_codex(original) if host == "codex" else original
                        )
                        self.apply(update=True)
                finally:
                    source.write_bytes(original)
                self.assertFalse(owned.exists())
                self.assertNotIn(owned.relative_to(self.app).as_posix(), self.manifest()["files"])
                self.assertEqual(unrelated.read_text(), "preserve the team's own role")

    def test_renamed_owned_agents_replace_only_the_previous_owned_role(self) -> None:
        """A canonical role rename removes the old file and installs the new source definition."""
        for host, extension in (("codex", ".toml"),):
            with self.subTest(host=host):
                self.app = self.base / f"renamed-role-{host}"
                self.apply(skills=["documentation-skill"], target=host)
                directory = self.app / project.HOST_DIRECTORIES[host]
                owned = directory / f"documentation-agent{extension}"
                unrelated = directory / f"team-owned-agent{extension}"
                unrelated.write_text("preserve the team's own role")
                source = self.source / "agents" / host / owned.name
                original = source.read_bytes()
                replacement = source.with_name(f"documentation-guide-agent{extension}")
                source.rename(replacement)
                replacement.write_bytes(
                    original.replace(b"documentation_agent", b"documentation_guide_agent")
                )
                try:
                    with patch.dict(
                        install.AGENTS[host], {"documentation-skill": [replacement.name]}
                    ):
                        self.apply(update=True)
                finally:
                    replacement.unlink()
                    source.write_bytes(original)
                self.assertFalse(owned.exists())
                self.assertTrue((directory / replacement.name).is_file())
                self.assertNotIn(owned.relative_to(self.app).as_posix(), self.manifest()["files"])
                self.assertEqual(unrelated.read_text(), "preserve the team's own role")

    def test_update_write_failure_restores_previous_content(self) -> None:
        """A late update failure restores old owned bytes and preserves external instructions."""
        self.apply(skills=["documentation-skill"])
        source_file = self.source / "skills/documentation-skill/SKILL.md"
        source_file.write_text(source_file.read_text() + "\nNew source guidance.\n")
        instructions = self.app / "AGENTS.md"
        instructions.write_bytes(b"user prefix\n" + instructions.read_bytes())
        before = {name: value[2] for name, value in self.snapshot().items()}
        write = project.write_file

        def fail(path: Path, state: project.FileState) -> None:
            if path.name == "manifest.json":
                raise OSError("simulated manifest failure")
            write(path, state)

        with patch.object(project, "write_file", side_effect=fail):
            with self.assertRaisesRegex(project.BootstrapError, "rolled back"):
                self.apply(update=True)
        self.assertEqual({name: value[2] for name, value in self.snapshot().items()}, before)

    def test_hostile_manifest_paths_cannot_escape_owned_roots(self) -> None:
        """An edited ownership record cannot authorize reads or writes outside toolkit paths."""
        self.apply(skills=["documentation-skill"], target="codex")
        manifest_path = self.app / project.MANIFEST
        original = manifest_path.read_bytes()
        for path in (
            "../../outside.txt",
            "/tmp/outside.txt",
            "AGENTS.md",
            ".agents/skills/documentation-skill/../../../app.py",
            ".codex/agents/ambiguous.toml",
            ".codex/agents/extra-agent.toml/child",
            ".codex/agents/extra-agent.agent.md",
            ".codex/agents/Extra-agent.toml",
            ".github/agents/documentation-agent.agent.md",
        ):
            with self.subTest(path=path):
                manifest = json.loads(original)
                manifest["files"][path] = "0" * 64
                manifest_path.write_text(json.dumps(manifest))
                before = self.snapshot()
                with self.assertRaisesRegex(project.BootstrapError, "Invalid owned path"):
                    self.apply(update=True)
                self.assertEqual(self.snapshot(), before)
        manifest_path.write_bytes(original)

    def test_symlinked_ancestor_and_destination_are_rejected(self) -> None:
        """Project writes never follow a managed path or project-root symlink."""
        external = self.base / "outside"
        external.mkdir()
        self.app.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(project.BootstrapError, "real directory"):
            self.apply()
        self.assertEqual(list(external.iterdir()), [])
        self.app.unlink()
        self.app.mkdir()
        (self.app / ".agents").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(project.BootstrapError, "real directory"):
            self.apply()
        self.assertEqual(list(external.iterdir()), [])
        (self.app / ".agents").unlink()
        (self.app / "AGENTS.md").symlink_to(external / "missing")
        with self.assertRaisesRegex(project.BootstrapError, "regular file"):
            self.apply()
        self.assertEqual(list(external.iterdir()), [])

    def test_source_overlap_rejected_and_separate_nested_source_supported(self) -> None:
        """Vendored source is allowed only outside all managed project destinations."""
        with self.assertRaisesRegex(project.BootstrapError, "overlap"):
            project.bootstrap(
                self.source,
                self.source,
                install.inventory(self.source),
                install.AGENTS,
                install.IGNORED,
            )
        self.app.mkdir()
        nested = self.app / "vendor/toolkit"
        nested.parent.mkdir()
        self.source.rename(nested)
        self.source = nested
        self.apply(skills=["documentation-skill"])
        self.assertTrue((self.app / ".agents/skills/documentation-skill/SKILL.md").is_file())
        self.assertTrue((self.source / "skills/documentation-skill/SKILL.md").is_file())

    def test_source_git_provenance_is_honest_about_dirty_and_nested_archive(self) -> None:
        """Only the source's own Git root supplies a revision; archives use content hashes."""
        subprocess.run(["git", "init", "-q", str(self.base)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.base),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-qm",
                "outer project",
            ],
            check=True,
        )
        self.apply(skills=["documentation-skill"])
        self.assertIsNone(self.manifest()["source"]["commit"])
        self.assertIsNone(self.manifest()["source"]["dirty"])
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.source),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-qm",
                "source checkpoint",
            ],
            check=True,
        )
        self.apply(update=True)
        identity = self.manifest()["source"]
        self.assertEqual(len(identity["commit"]), 40)
        self.assertTrue(identity["dirty"])
        previous_fingerprint = identity["content_sha256"]
        file = self.source / "skills/documentation-skill/SKILL.md"
        file.write_text(file.read_text() + "\nChanged source.\n")
        self.apply(update=True)
        self.assertNotEqual(self.manifest()["source"]["content_sha256"], previous_fingerprint)

    def test_generated_caches_are_not_copied(self) -> None:
        """Ignoring source caches matches package validation and avoids machine-specific state."""
        cache = self.source / "skills/documentation-skill/scripts/__pycache__"
        cache.mkdir()
        (cache / "private.pyc").write_bytes(b"generated cache")
        self.apply(skills=["documentation-skill"])
        self.assertFalse(list(self.app.rglob("*.pyc")))

    def test_unsupported_role_rendering_fails_before_writes(self) -> None:
        """A setting-like line inside instructions cannot be stripped as a top-level setting."""
        path = self.source / "agents/codex/documentation-agent.toml"
        text = path.read_text().replace(
            'developer_instructions = """',
            'developer_instructions = """\nmodel = an example in prose',
        )
        path.write_text(text)
        with self.assertRaisesRegex(project.BootstrapError, "Cannot safely render"):
            self.apply()
        self.assertFalse(self.app.exists())


if __name__ == "__main__":
    unittest.main()
