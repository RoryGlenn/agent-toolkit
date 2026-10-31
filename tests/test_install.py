"""Exercise the installer against disposable host directories and real package files."""

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

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
            skills or ["documentation-skill"],
            self.home,
            self.codex,
            backup_existing=backup_existing,
            dry_run=dry_run,
        )

    def list_catalog(self, *, json_output: bool = False) -> str:
        """Run the list command against the disposable package and host."""
        output = io.StringIO()
        with (
            patch.object(install, "ROOT", self.root),
            patch.object(Path, "home", side_effect=AssertionError("Listing must not read home")),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(install.main(["list", "--json"] if json_output else ["list"]), 0)
        return output.getvalue()

    def test_json_catalog_schema_and_current_metadata(self) -> None:
        """JSON contains exactly the public schema and actual runtime identifiers."""
        skills = install.inventory(self.root)
        with patch.object(install, "inventory", return_value=dict(reversed(skills.items()))):
            output = self.list_catalog(json_output=True)
        catalog = json.loads(output)
        self.assertEqual(set(catalog), {"schema_version", "skills"})
        self.assertEqual(type(catalog["schema_version"]), int)
        self.assertEqual(catalog["schema_version"], 1)
        self.assertEqual([entry["name"] for entry in catalog["skills"]], sorted(skills))
        entries = {entry["name"]: entry for entry in catalog["skills"]}
        for name, entry in entries.items():
            self.assertEqual(set(entry), {"name", "description", "dependencies", "roles"})
            self.assertEqual(entry["description"], skills[name])
            self.assertEqual(set(entry["roles"]), set(install.AGENTS))
            self.assertEqual(entry["roles"]["copilot"], [])
        self.assertEqual(
            entries["issue-to-tested-pr-skill"]["roles"]["codex"],
            ["adversarial_reviewer_agent", "implementation_owner_agent", "verifier_agent"],
        )
        self.assertEqual(entries["release-and-docs-skill"]["roles"]["codex"], [])
        self.assertEqual(entries["task-routing-skill"]["dependencies"], [])
        self.assertEqual(
            entries["ddia-assess-skill"]["dependencies"], ["ddia-skill", "task-routing-skill"]
        )

    def test_json_catalog_sorts_roles_and_exposes_only_direct_dependencies(self) -> None:
        """Unsorted associations and a dependency chain retain the JSON contract."""
        from project_bootstrap import SKILL_DEPENDENCIES

        associations = {host: dict(groups) for host, groups in install.AGENTS.items()}
        associations["codex"]["issue-to-tested-pr-skill"] = [
            "verifier-agent.toml",
            "implementation-owner-agent.toml",
            "adversarial-reviewer-agent.toml",
        ]
        with (
            patch.object(install, "AGENTS", associations),
            patch.dict(
                SKILL_DEPENDENCIES,
                {
                    "documentation-skill": ("issue-to-tested-pr-skill",),
                    "ddia-assess-skill": ("task-routing-skill", "ddia-skill"),
                },
            ),
        ):
            entries = {
                entry["name"]: entry
                for entry in json.loads(self.list_catalog(json_output=True))["skills"]
            }
        self.assertEqual(
            entries["documentation-skill"]["dependencies"], ["issue-to-tested-pr-skill"]
        )
        self.assertEqual(
            entries["ddia-assess-skill"]["dependencies"], ["ddia-skill", "task-routing-skill"]
        )
        self.assertEqual(
            entries["issue-to-tested-pr-skill"]["dependencies"], ["task-routing-skill"]
        )
        self.assertEqual(
            entries["issue-to-tested-pr-skill"]["roles"]["codex"],
            ["adversarial_reviewer_agent", "implementation_owner_agent", "verifier_agent"],
        )

    def test_json_catalog_escapes_description_text(self) -> None:
        """Quotes, backslashes, and Unicode round trip from current skill metadata."""
        path = self.root / "skills/documentation-skill/SKILL.md"
        text = path.read_text()
        description = 'Describe "quoted" paths \\ and café.'
        path.write_text(
            re.sub(r"(?m)^description: .*", f"description: {description}", text, count=1)
        )
        entries = json.loads(self.list_catalog(json_output=True))["skills"]
        self.assertEqual(
            next(
                entry["description"] for entry in entries if entry["name"] == "documentation-skill"
            ),
            description,
        )

    def test_json_catalog_rejects_invalid_sources_without_stdout(self) -> None:
        """Bad role metadata and missing required skills fail before producing JSON."""
        role = self.root / "agents/codex/documentation-agent.toml"
        original = role.read_text()
        for invalid in ("role", "dependency"):
            with self.subTest(invalid=invalid):
                if invalid == "role":
                    role.write_text(
                        original.replace('name = "documentation_agent"', 'name = "stale"')
                    )
                else:
                    role.write_text(original)
                    shutil.rmtree(self.root / "skills/task-routing-skill")
                output, errors = io.StringIO(), io.StringIO()
                with (
                    patch.object(install, "ROOT", self.root),
                    contextlib.redirect_stdout(output),
                    contextlib.redirect_stderr(errors),
                ):
                    self.assertEqual(install.main(["list", "--json"]), 1)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("error:", errors.getvalue())

    def test_json_catalog_fresh_process_does_not_create_source_cache(self) -> None:
        """A normal fresh CLI invocation creates no source cache or host state."""
        for name in ("install.py", "project_bootstrap.py"):
            shutil.copyfile(ROOT / name, self.root / name)
        before = set(self.root.rglob("*"))
        result = subprocess.run(
            [sys.executable, str(self.root / "install.py"), "list", "--json"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout)["schema_version"], 1)
        self.assertEqual(set(self.root.rglob("*")), before)
        self.assertFalse(self.home.exists())

    def test_list_shows_skill_only_and_shared_role_associations(self) -> None:
        """The catalog distinguishes no role, specialist roles, and shared workflow roles."""
        output = self.list_catalog()
        lines = output.splitlines()
        skills = install.inventory(self.root)
        entries = {
            name: lines[index + 1 : index + 3]
            for index, line in enumerate(lines)
            for name in skills
            if line.startswith(f"{name}: ")
        }
        self.assertEqual(set(entries), set(skills))
        self.assertEqual(
            entries["release-and-docs-skill"],
            ["  Codex roles: none (skill only)", "  Copilot roles: none (skill only)"],
        )
        self.assertEqual(
            entries["ddia-skill"],
            ["  Codex roles: ddia_agent", "  Copilot roles: none (skill only)"],
        )
        self.assertEqual(
            entries["documentation-skill"],
            ["  Codex roles: documentation_agent", "  Copilot roles: none (skill only)"],
        )
        self.assertEqual(
            entries["independent-diff-review-skill"],
            [
                "  Codex roles: adversarial_reviewer_agent, verifier_agent",
                "  Copilot roles: none (skill only)",
            ],
        )
        self.assertEqual(
            entries["issue-to-tested-pr-skill"],
            [
                "  Codex roles: adversarial_reviewer_agent, "
                "implementation_owner_agent, verifier_agent",
                "  Copilot roles: none (skill only)",
            ],
        )

    def test_copilot_catalog_contains_skills_without_agent_definitions(self) -> None:
        """A skill-only target does not require a source role directory."""
        self.assertEqual(install.AGENTS["copilot"], {})
        self.assertFalse((self.root / "agents/copilot").exists())
        output = self.list_catalog()
        self.assertIn("  Codex roles: documentation_agent\n", output)
        self.assertNotIn("Copilot roles: Documentation Agent", output)

    def test_skill_name_requires_type_suffix(self) -> None:
        """Matching frontmatter and directory cannot introduce an ambiguous skill name."""
        path = self.root / "skills/simplify-or-delete-skill"
        path.rename(path.with_name("simplify-or-delete"))
        path = path.with_name("simplify-or-delete") / "SKILL.md"
        path.write_text(path.read_text().replace("simplify-or-delete-skill", "simplify-or-delete"))
        with self.assertRaisesRegex(install.InstallError, "Invalid skill directory"):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_skill_display_metadata_and_prompts_use_canonical_names(self) -> None:
        """The skill picker and suggested invocation expose the same explicit skill identity."""
        for path in (self.root / "skills").glob("*/agents/openai.yaml"):
            with self.subTest(path=path):
                metadata = yaml.safe_load(path.read_text())["interface"]
                self.assertTrue(metadata["display_name"].endswith(" Skill"))
                invocations = re.findall(
                    r"\$([a-z0-9]+(?:-[a-z0-9]+)*)(?![\w-])", metadata["default_prompt"]
                )
                self.assertIn(path.parents[1].name, invocations)

    def test_codex_role_identifier_must_match_filename(self) -> None:
        """A suffixed filename cannot conceal a stale runtime role identifier."""
        path = self.root / "agents/codex/documentation-agent.toml"
        path.write_text(
            path.read_text().replace('name = "documentation_agent"', 'name = "doc_agent"')
        )
        with self.assertRaisesRegex(install.InstallError, "name must match its filename"):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_unmapped_agent_files_are_validated(self) -> None:
        """The naming gate includes files absent from installer associations."""
        path = self.root / "agents/codex/extra.toml"
        path.write_text('name = "extra"')
        with self.assertRaisesRegex(install.InstallError, "filename must end"):
            install.inventory(self.root)
        path.unlink()
        source = self.root / "agents/codex/documentation-agent.toml"
        path = path.with_name("extra-agent.toml")
        path.write_text(source.read_text().replace("documentation_agent", "extra_agent"))
        with self.assertRaisesRegex(install.InstallError, "unmapped.*extra-agent"):
            install.inventory(self.root)

    def test_copilot_role_files_are_rejected_as_unshipped_format(self) -> None:
        """The package cannot silently reintroduce a second agent-definition format."""
        path = self.root / "agents/copilot/documentation-agent.agent.md"
        path.parent.mkdir()
        path.write_text("---\nname: Documentation Agent\ndescription: Legacy fixture\n---\n")
        with self.assertRaisesRegex(install.InstallError, "Only Codex"):
            install.inventory(self.root)

    def seed_old_documentation_install(self, target: str = "codex") -> list[Path]:
        """Create old source-linked entries while retaining their source checkout."""
        previous = self.base / f"previous-{target}"
        skill_source = previous / "skills/doc-agent"
        shutil.copytree(self.root / "skills/documentation-skill", skill_source)
        metadata = skill_source / "SKILL.md"
        metadata.write_text(metadata.read_text().replace("documentation-skill", "doc-agent"))
        extension = ".toml" if target == "codex" else ".agent.md"
        agent_source = previous / "agents" / f"doc-agent{extension}"
        agent_source.parent.mkdir()
        if target == "codex":
            shutil.copyfile(self.root / "agents/codex/documentation-agent.toml", agent_source)
        else:
            fixture = json.loads(
                (ROOT / "tests/fixtures/pre-routing-copilot-project.json").read_text()
            )
            agent_source.write_text(
                fixture["files"][".github/agents/documentation-agent.agent.md"]["text"]
            )
        agent_source.write_text(
            agent_source.read_text()
            .replace("documentation-skill", "doc-agent")
            .replace("documentation_agent", "doc_agent")
            .replace("Documentation Agent", "Doc Agent")
        )
        paths = install.locations(self.home, self.codex)
        skill = paths[f"{target}-skills"] / "doc-agent"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.symlink_to(skill_source, target_is_directory=True)
        agent = paths[f"{target}-agents"] / agent_source.name
        agent.parent.mkdir(parents=True, exist_ok=True)
        if target == "codex":
            os.link(agent_source, agent)
        else:
            agent.symlink_to(agent_source)
        old = [skill, agent]
        if target == "codex":
            legacy = paths["legacy-codex-skills"] / "doc-agent"
            legacy.parent.mkdir(parents=True)
            legacy.symlink_to("../missing-old-source")
            old.append(legacy)
        return old

    def test_deprecated_cli_selector_installs_only_canonical_names(self) -> None:
        """Old commands remain usable without installing duplicate host aliases."""
        errors = io.StringIO()
        with patch.object(install, "ROOT", self.root), contextlib.redirect_stderr(errors):
            result = install.main(
                [
                    "install",
                    "--target",
                    "codex",
                    "--home",
                    str(self.home),
                    "--skill",
                    "doc-agent",
                    "--skill",
                    "documentation-skill",
                ]
            )
        self.assertEqual(result, 0)
        self.assertIn(
            "Deprecated skill selector 'doc-agent'; use 'documentation-skill'", errors.getvalue()
        )
        self.assertEqual(
            [path.name for path in (self.home / ".agents/skills").iterdir()],
            ["documentation-skill", "task-routing-skill"],
        )
        self.assertEqual(
            [path.name for path in (self.codex / "agents").iterdir()],
            ["documentation-agent.toml"],
        )

    def test_selected_rename_migration_and_restore_both_hosts(self) -> None:
        """Selected old entries move into a reversible backup; other skills stay intact."""
        for target in ("codex", "copilot"):
            with self.subTest(target=target):
                old = self.seed_old_documentation_install(target)
                identities = [path.lstat().st_ino for path in old]
                paths = install.locations(self.home, self.codex)
                unselected = paths[f"{target}-skills"] / "unselected-custom-skill"
                unselected.mkdir()
                (unselected / "custom.md").write_text("preserve unselected")
                receipt = self.apply(target=target, backup_existing=True)
                assert receipt is not None
                retired = old if target == "codex" else old[:1]
                self.assertTrue(all(not install.present(path) for path in retired))
                if target == "copilot":
                    self.assertTrue(old[1].is_symlink())
                    self.assertEqual(old[1].lstat().st_ino, identities[1])
                skill = paths[f"{target}-skills"] / "documentation-skill"
                self.assertTrue(skill.is_symlink())
                self.assertEqual((unselected / "custom.md").read_text(), "preserve unselected")
                install.restore(receipt, dry_run=True)
                self.assertTrue(skill.is_symlink())
                install.restore(receipt)
                self.assertEqual([path.lstat().st_ino for path in old], identities)
                self.assertTrue((old[0] / "SKILL.md").is_file())
                self.assertFalse(install.present(skill))

    def test_rename_conflict_and_dry_run_preserve_old_entries(self) -> None:
        """Renaming cannot modify existing entries without backup or during preview."""
        old = self.seed_old_documentation_install()
        identities = [path.lstat().st_ino for path in old]
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        self.apply(backup_existing=True, dry_run=True)
        self.assertEqual([path.lstat().st_ino for path in old], identities)
        self.assertFalse(install.present(self.home / ".agents/skills/documentation-skill"))
        self.assertFalse((self.home / ".local").exists())

    def test_rename_migration_failure_restores_old_entries(self) -> None:
        """A failure after all rename moves restores old links and hard-link identities."""
        old = self.seed_old_documentation_install()
        identities = [path.lstat().st_ino for path in old]
        write = install.write_receipt

        def fail(path: Path, data: dict[str, object]) -> None:
            if data["state"] == "installed":
                raise OSError("simulated final receipt failure")
            write(path, data)

        with patch.object(install, "write_receipt", side_effect=fail):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                self.apply(backup_existing=True)
        self.assertEqual([path.lstat().st_ino for path in old], identities)
        self.assertFalse(install.present(self.home / ".agents/skills/documentation-skill"))
        self.assertFalse(install.present(self.codex / "agents/documentation-agent.toml"))

    def test_all_old_selectors_migrate_shared_roles_once(self) -> None:
        """A full upgrade removes old names, deduplicates shared roles, and restores all."""
        paths = install.locations(self.home, self.codex)
        old = []
        for area, names in (
            ("codex-skills", install.SKILL_ALIASES),
            ("legacy-codex-skills", install.SKILL_ALIASES),
            ("codex-agents", install.AGENT_ALIASES["codex"]),
        ):
            paths[area].mkdir(parents=True)
            for name in names:
                path = paths[area] / name
                path.write_text(f"preserve {area}/{name}")
                old.append(path)
        with contextlib.redirect_stderr(io.StringIO()):
            receipt = self.apply(list(install.SKILL_ALIASES), backup_existing=True)
        assert receipt is not None
        self.assertTrue(all(not install.present(path) for path in old))
        self.assertEqual(
            {path.name for path in paths["codex-skills"].iterdir()},
            set(install.SKILL_ALIASES.values()) | {"task-routing-skill"},
        )
        self.assertEqual(len(list(paths["codex-agents"].iterdir())), 6)
        self.assertTrue(
            all(path.name.endswith("-skill") for path in paths["codex-skills"].iterdir())
        )
        entries = json.loads(receipt.read_text())["entries"]
        self.assertEqual(len(entries), len({(entry["area"], entry["name"]) for entry in entries}))
        install.restore(receipt)
        for path in old:
            self.assertTrue(path.read_text().startswith("preserve "))

    def test_list_does_not_change_package_or_host(self) -> None:
        """Listing available capabilities preserves package files and existing host state."""
        marker = self.codex / "agents/unrelated.toml"
        marker.parent.mkdir(parents=True)
        marker.write_text("unrelated host state")

        def snapshot() -> dict[Path, tuple[int, int, bytes | None]]:
            """Capture directory entries and file contents without access-time metadata."""
            return {
                path.relative_to(self.base): (
                    path.stat().st_ino,
                    path.stat().st_mtime_ns,
                    path.read_bytes() if path.is_file() else None,
                )
                for path in self.base.rglob("*")
            }

        before = snapshot()
        self.list_catalog()
        self.list_catalog(json_output=True)
        self.assertEqual(snapshot(), before)

    def test_selected_install_links_canonical_skill_and_agent(self) -> None:
        """A selected docs install exposes the complete skill and its wrapper."""
        receipt = self.apply()
        self.assertIsNotNone(receipt)
        skill = self.home / ".agents/skills/documentation-skill"
        self.assertEqual(skill.resolve(), self.root / "skills/documentation-skill")
        self.assertTrue((skill / "references/book-foundation.md").is_file())
        role = self.codex / "agents/documentation-agent.toml"
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(self.root / "agents/codex/documentation-agent.toml"))
        with os.fdopen(os.open(role, os.O_RDONLY | os.O_NOFOLLOW)) as handle:
            self.assertIn('name = "documentation_agent"', handle.read())
        self.assertFalse((self.home / ".agents/skills/release-and-docs-skill").exists())
        (self.root / "skills/documentation-skill/local-example.md").write_text("new content")
        self.assertEqual((skill / "local-example.md").read_text(), "new content")

    def test_all_skills_and_associated_agents_for_both_hosts(self) -> None:
        """Each host receives the authoritative skill inventory and supported wrappers."""
        skills = list(install.inventory(self.root))
        self.apply(skills)
        self.apply(skills, target="copilot")
        self.assertEqual(
            {path.name for path in (self.home / ".agents/skills").iterdir()}, set(skills)
        )
        self.assertEqual(len(list((self.codex / "agents").iterdir())), 6)
        self.assertEqual(
            {path.name for path in (self.home / ".copilot/skills").iterdir()}, set(skills)
        )
        self.assertFalse((self.home / ".copilot/agents").exists())

    def test_skill_only_install_preserves_roles_and_restores_independently(self) -> None:
        """A skill-only workflow installs without changing existing specialists."""
        self.apply(["ddia-skill", "software-design-skill"])
        roles = {
            path.name: (path.stat().st_ino, path.read_bytes())
            for path in (self.codex / "agents").iterdir()
        }
        receipt = self.apply(["release-and-docs-skill"])
        assert receipt is not None
        skill = self.home / ".agents/skills/release-and-docs-skill"
        self.assertEqual(skill.resolve(), self.root / "skills/release-and-docs-skill")
        self.assertIsNone(self.apply(["release-and-docs-skill"]))
        self.assertEqual(
            {
                path.name: (path.stat().st_ino, path.read_bytes())
                for path in (self.codex / "agents").iterdir()
            },
            roles,
        )
        install.restore(receipt)
        self.assertFalse(install.present(skill))
        self.assertTrue((self.home / ".agents/skills/ddia-skill").is_symlink())
        self.assertTrue((self.home / ".agents/skills/software-design-skill").is_symlink())
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
        role = self.codex / "agents/documentation-agent.toml"
        source = self.root / "agents/codex/documentation-agent.toml"
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
        source = self.root / "agents/codex/documentation-agent.toml"
        role = self.codex / "agents/documentation-agent.toml"
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
        installed = self.home / ".agents/skills/documentation-skill"
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
        conflict = self.codex / "agents/documentation-agent.toml"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("local instructions")
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        self.assertEqual(conflict.read_text(), "local instructions")
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".local").exists())

    def test_backup_restore_roundtrip_preserves_directory_file_and_broken_link(self) -> None:
        """Migration retains different destination types and unrelated settings."""
        skill = self.home / ".agents/skills/documentation-skill"
        skill.mkdir(parents=True)
        (skill / "custom.md").write_text("custom skill")
        agent = self.codex / "agents/documentation-agent.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text("custom agent")
        legacy = self.codex / "skills/documentation-skill"
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
        legacy = self.codex / "skills/documentation-skill"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("old")
        with self.assertRaisesRegex(install.InstallError, "Existing entries"):
            self.apply()
        self.assertFalse((self.home / ".agents").exists())

    def test_broken_destination_link_conflicts(self) -> None:
        """Dangling links are treated as user content, not empty destinations."""
        destination = self.home / ".agents/skills/documentation-skill"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(self.base / "missing")
        with self.assertRaises(install.InstallError):
            self.apply()
        self.assertTrue(destination.is_symlink())

    def test_source_symlink_is_rejected_before_writes(self) -> None:
        """An internal source link never exposes unrelated files to the host."""
        (self.root / "skills/documentation-skill/private").symlink_to(self.base / "missing")
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
        os.mkfifo(self.root / "skills/documentation-skill/pipe")
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
        (self.root / "skills/documentation-skill/SKILL.md").write_text("missing metadata")
        with self.assertRaisesRegex(install.InstallError, "frontmatter"):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_late_link_failure_rolls_back_backups_and_new_directories(self) -> None:
        """An ordinary write failure restores all earlier user entries."""
        legacy = self.codex / "skills/documentation-skill"
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
        legacy = self.codex / "skills/documentation-skill"
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
        agent = self.codex / "agents/documentation-agent.toml"
        agent.unlink()
        agent.write_text("new local work")
        with self.assertRaisesRegex(install.InstallError, "has changed"):
            install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/documentation-skill").is_symlink())
        self.assertEqual(agent.read_text(), "new local work")

    def test_restore_refuses_missing_backup_before_any_changes(self) -> None:
        """An incomplete backup cannot cause partial restoration."""
        legacy = self.codex / "skills/documentation-skill"
        legacy.mkdir(parents=True)
        receipt = self.apply(backup_existing=True)
        assert receipt is not None
        (receipt.parent / "2").rmdir()
        with self.assertRaisesRegex(install.InstallError, "backup is missing"):
            install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/documentation-skill").is_symlink())

    def test_restore_failure_reinstates_installed_links(self) -> None:
        """An ordinary restoration failure leaves the completed install usable."""
        receipt = self.apply()
        assert receipt is not None
        with patch.object(install, "write_receipt", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(install.InstallError, "rolled back"):
                install.restore(receipt)
        self.assertTrue((self.home / ".agents/skills/documentation-skill").is_symlink())
        self.assertTrue(
            (self.codex / "agents/documentation-agent.toml").samefile(
                self.root / "agents/codex/documentation-agent.toml"
            )
        )
        self.assertFalse((self.codex / "agents/documentation-agent.toml").is_symlink())
        self.assertEqual(json.loads(receipt.read_text())["state"], "installed")

    def test_restore_fresh_install_removes_only_toolkit_links(self) -> None:
        """Restoring a fresh install preserves unrelated host files."""
        receipt = self.apply()
        assert receipt is not None
        unrelated = self.codex / "config.toml"
        unrelated.write_text("keep")
        install.restore(receipt)
        self.assertFalse(install.present(self.home / ".agents/skills/documentation-skill"))
        self.assertFalse(install.present(self.codex / "agents/documentation-agent.toml"))
        self.assertEqual(unrelated.read_text(), "keep")

    def test_custom_codex_home(self) -> None:
        """A custom Codex home changes agent and legacy paths, not shared skills."""
        self.codex = self.base / "custom codex"
        self.apply()
        self.assertTrue(
            (self.codex / "agents/documentation-agent.toml").samefile(
                self.root / "agents/codex/documentation-agent.toml"
            )
        )
        self.assertTrue((self.home / ".agents/skills/documentation-skill").is_symlink())
        self.assertFalse((self.home / ".codex").exists())

    def test_codex_home_cannot_retire_canonical_source(self) -> None:
        """A Codex home equal to the checkout cannot move its source skills."""
        self.codex = self.root
        skill = self.root / "skills/documentation-skill/SKILL.md"
        before = skill.read_bytes()
        with self.assertRaisesRegex(install.InstallError, "overlap"):
            self.apply(backup_existing=True)
        self.assertEqual(skill.read_bytes(), before)
        self.assertFalse((self.root / "skills/documentation-skill").is_symlink())
        self.assertFalse(self.home.exists())

    def test_aliasing_legacy_location_cannot_remove_installed_skill(self) -> None:
        """A repeat install cannot mistake its active skill for a legacy copy."""
        self.apply()
        skill = self.home / ".agents/skills/documentation-skill"
        before = skill.lstat()
        receipts = list((self.home / ".local/state/agent-toolkit/installations").iterdir())
        self.codex = self.home / ".agents"
        with self.assertRaisesRegex(install.InstallError, "overlap"):
            self.apply(backup_existing=True)
        self.assertEqual(skill.lstat().st_ino, before.st_ino)
        self.assertEqual(skill.resolve(), self.root / "skills/documentation-skill")
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
        self.apply(["independent-diff-review-skill"])
        self.assertEqual(
            sorted(path.name for path in (self.codex / "agents").iterdir()),
            ["adversarial-reviewer-agent.toml", "verifier-agent.toml"],
        )
        self.assertFalse((self.home / ".agents/skills/issue-to-tested-pr-skill").exists())

    def test_shared_agent_dependencies_are_installed_once(self) -> None:
        """Combined workflow selections produce one receipt entry per destination."""
        selected = ["independent-diff-review-skill", "issue-to-tested-pr-skill"]
        receipt = self.apply(selected)
        assert receipt is not None
        entries = json.loads(receipt.read_text())["entries"]
        destinations = [(entry["area"], entry["name"]) for entry in entries]
        self.assertEqual(len(destinations), 6)
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
                "documentation-skill",
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
            (self.codex / "agents/documentation-agent.toml").samefile(
                ROOT / "agents/codex/documentation-agent.toml"
            )
        )
        self.assertFalse(outside.exists())

    def run_status(self, *options: str, target: str = "codex") -> tuple[int, str, str]:
        """Capture the status CLI against the disposable checkout and explicit home."""
        output, errors = io.StringIO(), io.StringIO()
        with (
            patch.object(install, "ROOT", self.root),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(errors),
        ):
            code = install.main(["status", "--target", target, "--home", str(self.home), *options])
        return code, output.getvalue(), errors.getvalue()

    def status_snapshot(self) -> dict[Path, tuple[int, int, int, int, str | bytes | None]]:
        """Capture entry identity, mode, modification time, targets and file bytes."""
        result = {}
        for path in self.base.rglob("*"):
            metadata = path.lstat()
            content = (
                os.readlink(path)
                if path.is_symlink()
                else path.read_bytes()
                if path.is_file()
                else None
            )
            result[path.relative_to(self.base)] = (
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_mtime_ns,
                metadata.st_nlink,
                content,
            )
        return result

    def test_status_missing_home_and_invalid_selection_do_not_write(self) -> None:
        """Missing and invalid inspections emit one JSON object without creating a home."""
        before = self.status_snapshot()
        code, output, errors = self.run_status("--skill", "documentation-skill", "--json")
        self.assertEqual(code, 1)
        self.assertEqual(errors, "")
        self.assertEqual(
            json.loads(output),
            {
                "schema_version": 1,
                "entries": [
                    {
                        "area": "codex-agents",
                        "name": "documentation-agent.toml",
                        "state": "missing",
                    },
                    {"area": "codex-skills", "name": "documentation-skill", "state": "missing"},
                    {"area": "codex-skills", "name": "task-routing-skill", "state": "missing"},
                ],
            },
        )
        code, output, errors = self.run_status("--skill", "unknown-skill", "--json")
        self.assertEqual(code, 1)
        self.assertIn("Unknown skills", errors)
        self.assertEqual(json.loads(output)["entries"], [])
        self.assertIn("Unknown skills", json.loads(output)["error"])
        self.assertFalse(self.home.exists())
        self.assertEqual(self.status_snapshot(), before)

    def test_status_all_current_both_hosts_is_sorted_and_read_only(self) -> None:
        """All inspects every expected entry once and Copilot never expects roles."""
        skills = list(install.inventory(self.root))
        for target in ("codex", "copilot"):
            self.apply(skills, target=target)
        before = self.status_snapshot()
        for target in ("codex", "copilot"):
            with self.subTest(target=target):
                code, output, errors = self.run_status("--all", "--json", target=target)
                self.assertEqual(code, 0, errors)
                payload = json.loads(output)
                self.assertEqual(payload["schema_version"], 1)
                entries = payload["entries"]
                keys = [(entry["area"], entry["name"]) for entry in entries]
                self.assertEqual(keys, sorted(set(keys)))
                self.assertTrue(all(set(entry) == {"area", "name", "state"} for entry in entries))
                self.assertTrue(all(entry["state"] == "current" for entry in entries))
                self.assertEqual(
                    {entry["name"] for entry in entries if entry["area"] == f"{target}-skills"},
                    set(skills),
                )
                self.assertEqual(len(entries), len(skills) + (6 if target == "codex" else 0))
        self.assertEqual(self.status_snapshot(), before)

    def test_status_json_argument_errors_emit_one_object(self) -> None:
        """Invalid CLI selections preserve the machine-readable output contract."""
        before = self.status_snapshot()
        for options in (
            ["--json"],
            ["--all", "--skill", "documentation-skill", "--json"],
            ["--all", "--json", "--unexpected"],
        ):
            with self.subTest(options=options):
                code, output, errors = self.run_status(*options)
                self.assertNotEqual(code, 0)
                self.assertIn("error:", errors)
                payload = json.loads(output)
                self.assertEqual(payload["schema_version"], 1)
                self.assertEqual(payload["entries"], [])
                self.assertIn("error", payload)
        code, output, errors = self.run_status("--all", "--json", target="unknown")
        self.assertNotEqual(code, 0)
        self.assertIn("invalid choice", errors)
        self.assertEqual(json.loads(output)["entries"], [])
        self.assertEqual(self.status_snapshot(), before)

    def test_status_json_symlink_loop_homes_fail_without_writes(self) -> None:
        """Real CLI filesystem errors preserve JSON output and the inspected trees."""
        for name in ("install.py", "project_bootstrap.py"):
            shutil.copyfile(ROOT / name, self.root / name)
        loop = self.base / "loop"
        loop.symlink_to(loop.name)
        before = self.status_snapshot()
        for option in ("--home", "--codex-home"):
            with self.subTest(option=option):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(self.root / "install.py"),
                        "status",
                        "--target",
                        "codex",
                        "--skill",
                        "documentation-skill",
                        "--home",
                        str(self.home),
                        option,
                        str(loop),
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("error:", result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["schema_version"], 1)
                self.assertEqual(payload["entries"], [])
                self.assertIn("loop", payload["error"].lower())
                self.assertEqual(self.status_snapshot(), before)

    def test_status_aliases_dependencies_and_shared_roles_are_unique(self) -> None:
        """Repeated canonical/alias selectors include dependency closure and shared roles."""
        options = [
            "--skill",
            "issue-to-tested-pr",
            "--skill",
            "issue-to-tested-pr-skill",
            "--skill",
            "independent-diff-review",
            "--skill",
            "ddia-migrate-skill",
            "--json",
        ]
        code, output, errors = self.run_status(*options)
        self.assertEqual(code, 1)
        self.assertIn("Deprecated skill selector", errors)
        entries = json.loads(output)["entries"]
        keys = [(entry["area"], entry["name"]) for entry in entries]
        self.assertEqual(keys, sorted(set(keys)))
        self.assertEqual(
            {name for area, name in keys if area == "codex-skills"},
            {
                "issue-to-tested-pr-skill",
                "independent-diff-review-skill",
                "task-routing-skill",
                "ddia-skill",
                "ddia-migrate-skill",
            },
        )
        self.assertEqual(len(entries), 9)

    def test_status_role_requires_current_regular_hardlink(self) -> None:
        """Equal bytes do not make copies, symlinks or atomically detached roles current."""
        self.apply()
        role = self.codex / "agents/documentation-agent.toml"
        source = self.root / "agents/codex/documentation-agent.toml"
        for kind in ("copy", "symlink", "stale-hardlink", "foreign-hardlink"):
            with self.subTest(kind=kind):
                role.unlink()
                if kind == "copy":
                    shutil.copyfile(source, role)
                elif kind == "symlink":
                    role.symlink_to(source)
                elif kind == "foreign-hardlink":
                    foreign = self.base / "foreign-role.toml"
                    shutil.copyfile(source, foreign)
                    os.link(foreign, role)
                else:
                    os.link(source, role)
                    replacement = source.with_suffix(".replacement")
                    replacement.write_bytes(source.read_bytes())
                    replacement.replace(source)
                self.assertEqual(role.read_bytes(), source.read_bytes())
                before = self.status_snapshot()
                code, output, _ = self.run_status("--skill", "documentation-skill", "--json")
                self.assertEqual(code, 1)
                self.assertEqual(json.loads(output)["entries"][0]["state"], "different")
                self.assertEqual(self.status_snapshot(), before)

    def test_status_foreign_skill_entries_are_different_without_repairs(self) -> None:
        """Copied directories, files and foreign/dangling/relative links remain untouched."""
        self.apply()
        skill = self.home / ".agents/skills/documentation-skill"
        source = self.root / "skills/documentation-skill"
        foreign = self.base / "foreign skill"
        shutil.copytree(source, foreign)
        for kind in ("copy", "file", "foreign", "dangling", "relative"):
            with self.subTest(kind=kind):
                if skill.is_symlink() or skill.is_file():
                    skill.unlink()
                else:
                    shutil.rmtree(skill)
                if kind == "copy":
                    shutil.copytree(source, skill)
                elif kind == "file":
                    skill.write_text("foreign entry")
                else:
                    target = {
                        "foreign": str(foreign),
                        "dangling": "/missing-source",
                        "relative": os.path.relpath(source, skill.parent),
                    }[kind]
                    skill.symlink_to(target, target_is_directory=True)
                before = self.status_snapshot()
                code, output, _ = self.run_status("--skill", "documentation-skill", "--json")
                self.assertEqual(code, 1)
                self.assertEqual(json.loads(output)["entries"][1]["state"], "different")
                self.assertEqual(self.status_snapshot(), before)

    def test_status_human_output_and_explicit_home_rules(self) -> None:
        """Explicit home ignores inherited Codex state while an explicit override is honored."""
        self.apply()
        custom = self.base / "custom codex"
        (custom / "agents").mkdir(parents=True)
        os.link(
            self.root / "agents/codex/documentation-agent.toml",
            custom / "agents/documentation-agent.toml",
        )
        unrelated = self.codex / "agents/unselected-agent.toml"
        unrelated.write_text("preserve unrelated role")
        legacy = self.home / ".agents/skills/doc-agent"
        legacy.symlink_to("/missing-old-source")
        with patch.dict(os.environ, {"CODEX_HOME": str(self.base / "inherited codex")}):
            before = self.status_snapshot()
            code, output, errors = self.run_status("--skill", "documentation-skill")
            self.assertEqual(code, 0, errors)
            self.assertEqual(len(output.splitlines()), 3)
            self.assertIn(f"{self.codex / 'agents/documentation-agent.toml'}: current", output)
            self.assertNotIn(str(legacy), output)
            code, output, errors = self.run_status(
                "--skill", "documentation-skill", "--codex-home", str(custom), "--json"
            )
            self.assertEqual(code, 0, errors)
            (custom / "agents/documentation-agent.toml").unlink()
            code, output, _ = self.run_status(
                "--skill", "documentation-skill", "--codex-home", str(custom), "--json"
            )
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output)["entries"][0]["state"], "missing")
            os.link(
                self.root / "agents/codex/documentation-agent.toml",
                custom / "agents/documentation-agent.toml",
            )
            # Recreated entries have new metadata, so compare only the untouched roots here.
            after = self.status_snapshot()
            for path, value in before.items():
                if path.parts[0] != custom.name:
                    self.assertEqual(after[path], value)
        self.assertFalse((self.base / "inherited codex").exists())

    def test_status_pristine_cli_does_not_create_source_bytecode(self) -> None:
        """The lazy dependency import is read-only even in an uncached source checkout."""
        for name in ("install.py", "project_bootstrap.py"):
            shutil.copyfile(ROOT / name, self.root / name)
        before = self.status_snapshot()
        environment = {
            key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"
        }
        result = subprocess.run(
            [
                sys.executable,
                str(self.root / "install.py"),
                "status",
                "--target",
                "codex",
                "--skill",
                "documentation-skill",
                "--home",
                str(self.home),
                "--json",
            ],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["entries"]), 3)
        self.assertFalse((self.root / "__pycache__").exists())
        self.assertEqual(self.status_snapshot(), before)

    def test_status_invalid_source_and_parent_fail_without_writes(self) -> None:
        """Status rejects invalid package data and symlinked destination parents."""
        real = self.base / "real skills"
        real.mkdir()
        (self.home / ".agents").mkdir(parents=True)
        (self.home / ".agents/skills").symlink_to(real, target_is_directory=True)
        before = self.status_snapshot()
        code, output, errors = self.run_status("--skill", "documentation-skill", "--json")
        self.assertEqual(code, 1)
        self.assertIn("Expected a real directory", errors)
        self.assertEqual(json.loads(output)["entries"], [])
        self.assertEqual(self.status_snapshot(), before)
        metadata = self.root / "skills/documentation-skill/SKILL.md"
        metadata.write_text("invalid source")
        before = self.status_snapshot()
        code, output, errors = self.run_status("--all", "--json")
        self.assertEqual(code, 1)
        self.assertIn("frontmatter", errors)
        self.assertEqual(json.loads(output)["entries"], [])
        self.assertEqual(self.status_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
