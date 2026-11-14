"""Exercise real Git histories and isolated personal installs without GitHub access."""

from __future__ import annotations

import contextlib
import fcntl
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import install
import toolkit_update as update

ROOT = Path(__file__).resolve().parents[1]


class FixtureUpdater(update.Updater):
    """Use a real fixture check instead of linting an intentionally tiny repo."""

    def deployment_checks(self, candidate: Path) -> list[list[str]]:
        return [[sys.executable, "check.py"]]


class UpdaterTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="toolkit-update-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.home = self.base / "test home"
        self.repo = self.home / "repos/toolkit"
        self.upstream = self.home / "repos/upstream"
        self.upstream.mkdir(parents=True)
        for name in ("skills", "agents"):
            shutil.copytree(
                ROOT / name,
                self.upstream / name,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
            )
        for name in (*update.RUNTIME_FILES, "systemd"):
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, self.upstream / name)
            else:
                shutil.copy2(source, self.upstream / name)
        (self.upstream / "check.py").write_text("raise SystemExit(0)\n")
        (self.upstream / ".gitignore").write_text("__pycache__/\n")
        self.raw_git(self.upstream, "init", "-b", "main")
        self.commit(self.upstream, "fixture baseline")
        self.raw_git(self.upstream.parent, "clone", str(self.upstream), str(self.repo))
        self.settings = update.Settings(
            self.repo, self.home, self.home / ".codex", Path(sys.executable), str(self.upstream)
        )
        self.updater = FixtureUpdater(self.settings)
        self.standalone = self.home / ".codex/skills/doc-agent/SKILL.md"
        self.standalone.parent.mkdir(parents=True)
        self.standalone.write_text("Original standalone Doc Agent.\n")
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        install.install(
            self.repo,
            "codex",
            list(install.inventory(self.repo)),
            self.home,
            self.settings.codex_home,
            backup_existing=False,
            dry_run=False,
            preserve_legacy_skills=("doc-agent",),
        )
        self.previous = update.git(self.repo, "rev-parse", "HEAD")
        self.original = self.updater.managed_snapshot()
        self.preserved = self.updater.preserved_snapshot()

    @staticmethod
    def raw_git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                *args,
            ],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

    def commit(self, root: Path, message: str) -> str:
        self.raw_git(root, "add", ".")
        self.raw_git(root, "commit", "-m", message)
        return self.raw_git(root, "rev-parse", "HEAD")

    def advance(self, *, fail: bool = False) -> str:
        role = self.upstream / "agents/codex/documentation-agent.toml"
        role.write_text(role.read_text() + "\n# Updated fixture definition.\n")
        skill = self.upstream / "skills/documentation-skill/SKILL.md"
        skill.write_text(skill.read_text() + "\nUpdated fixture guidance.\n")
        if fail:
            (self.upstream / "check.py").write_text("raise SystemExit(3)\n")
        return self.commit(self.upstream, "fixture update")

    def assert_current(self, revision: str) -> None:
        self.assertEqual(update.git(self.repo, "rev-parse", "HEAD"), revision)
        self.assertTrue(all(item["state"] == "current" for item in self.updater.entries(self.repo)))
        self.assertEqual(self.updater.preserved_snapshot(), self.preserved)

    def test_update_refreshes_regular_role_inodes_and_preserves_doc_agent(self) -> None:
        target = self.advance()
        role = self.settings.codex_home / "agents/documentation-agent.toml"
        inode = role.stat().st_ino
        result = self.updater.run()
        self.assertEqual(result["result"], "updated", result)
        self.assert_current(target)
        self.assertFalse(role.is_symlink())
        self.assertNotEqual(role.stat().st_ino, inode)
        self.assertTrue(role.samefile(self.repo / "agents/codex/documentation-agent.toml"))
        self.assertEqual(update.read_json(Path(result["receipt"]))["state"], "installed")
        self.assertEqual(self.updater.run()["result"], "current")

    def test_tracked_and_untracked_work_holds_without_fetch(self) -> None:
        for name in ("check.py", "unpublished.txt"):
            with self.subTest(name=name):
                path = self.repo / name
                original = path.read_bytes() if path.exists() else None
                path.write_text("local work\n")
                with patch.object(self.updater, "validate_candidate") as validate:
                    result = self.updater.run()
                self.assertEqual(result["result"], "blocked-local-changes")
                validate.assert_not_called()
                self.assertEqual(self.original, self.updater.managed_snapshot())
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

    def test_candidate_failure_keeps_live_source_and_inodes(self) -> None:
        self.advance(fail=True)
        result = self.updater.run()
        self.assertEqual(result["result"], "failed-validation", result)
        self.assert_current(self.previous)
        self.assertEqual(self.original, self.updater.managed_snapshot())
        self.assertEqual(
            update.read_json(Path(result["evidence"]) / "checks.json")["checks"][0]["exit_code"], 3
        )

    def test_divergent_local_commit_is_held(self) -> None:
        self.advance()
        (self.repo / "check.py").write_text("# local committed change\n")
        local = self.commit(self.repo, "fixture local divergence")
        result = self.updater.run()
        self.assertEqual(result["result"], "blocked-history", result)
        self.assert_current(local)

    def test_foreign_role_and_new_skill_collision_are_preserved(self) -> None:
        self.advance()
        role = self.settings.codex_home / "agents/documentation-agent.toml"
        replacement = role.with_suffix(".new")
        replacement.write_text("foreign definition")
        replacement.replace(role)
        result = self.updater.run()
        self.assertEqual(result["result"], "blocked-installation")
        self.assertEqual(role.read_text(), "foreign definition")

    def test_new_skill_collision_blocks_before_promotion(self) -> None:
        skill = self.upstream / "skills/new-example-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: new-example-skill\ndescription: Fixture.\n---\nExample.\n"
        )
        self.commit(self.upstream, "fixture new skill")
        foreign = self.home / ".agents/skills/new-example-skill"
        foreign.mkdir()
        (foreign / "keep.txt").write_text("personal work")
        result = self.updater.run()
        self.assertEqual(result["result"], "blocked-installation", result)
        self.assertEqual((foreign / "keep.txt").read_text(), "personal work")
        self.assert_current(self.previous)

    def test_concurrent_source_edit_is_preserved(self) -> None:
        self.advance()
        original = self.updater.validate_candidate

        def validate(candidate: Path, run: Path) -> list[dict[str, object]]:
            checks = original(candidate, run)
            (self.repo / "unpublished.txt").write_text("work during validation")
            return checks

        with patch.object(self.updater, "validate_candidate", side_effect=validate):
            result = self.updater.run()
        self.assertEqual(result["result"], "blocked-local-changes", result)
        self.assertEqual((self.repo / "unpublished.txt").read_text(), "work during validation")
        self.assertEqual(update.git(self.repo, "rev-parse", "HEAD"), self.previous)

    def test_verification_failure_rolls_back_and_relinks_prior_inodes(self) -> None:
        self.advance()
        verify = self.updater.verify_live
        calls = 0

        def fail_once(preserved: dict[str, object]) -> list[dict[str, str]]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise update.UpdateError("failed-verification", "Injected post-install failure")
            return verify(preserved)

        with patch.object(self.updater, "verify_live", side_effect=fail_once):
            result = self.updater.run()
        self.assertEqual(result["result"], "rolled-back", result)
        self.assert_current(self.previous)
        self.assertEqual(
            update.read_json(self.settings.state / "transaction.json")["phase"], "rolled-back"
        )

    def test_explicit_rollback_of_completed_update(self) -> None:
        self.advance()
        self.assertEqual(self.updater.run()["result"], "updated")
        result = self.updater.run(rollback=True)
        self.assertEqual(result["result"], "rollback-complete", result)
        self.assert_current(self.previous)

    def test_interrupted_promoted_transaction_recovers_on_next_run(self) -> None:
        self.advance()
        original = self.updater.install_from

        def interrupt_live(
            root: Path, home: Path, codex: Path, log: Path, *, receipt_id: str | None = None
        ) -> Path | None:
            if home == self.home:
                raise KeyboardInterrupt
            return original(root, home, codex, log, receipt_id=receipt_id)

        with patch.object(self.updater, "install_from", side_effect=interrupt_live):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        result = self.updater.run()
        self.assertEqual(result["result"], "recovered", result)
        self.assert_current(self.previous)

    def test_interrupted_transaction_refuses_subsequent_user_edits(self) -> None:
        self.advance()
        with patch.object(self.updater, "verify_live", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        (self.repo / "check.py").write_text("unpublished recovery work")
        result = self.updater.run()
        self.assertEqual(result["result"], "recovery-required", result)
        self.assertEqual((self.repo / "check.py").read_text(), "unpublished recovery work")

    def test_lock_contention_does_not_replace_last_result(self) -> None:
        self.updater.run()
        latest = (self.settings.state / "latest.json").read_bytes()
        with (self.settings.state / "update.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.updater.run()["result"], "busy")
        self.assertEqual((self.settings.state / "latest.json").read_bytes(), latest)

    def test_hidden_index_flags_are_rejected(self) -> None:
        self.raw_git(self.repo, "update-index", "--assume-unchanged", "check.py")
        (self.repo / "check.py").write_text("hidden local work")
        self.assertEqual(self.updater.run()["result"], "blocked-index-flags")

    def test_setup_fixed_runtime_is_idempotent_and_rejects_foreign_wrapper(self) -> None:
        config = update.setup(self.repo, self.home, Path(sys.executable))
        contents = config.read_bytes()
        wrapper = self.home / ".local/bin/agent-toolkit-update"
        before = wrapper.read_bytes()
        self.assertEqual(update.setup(self.repo, self.home, Path(sys.executable)), config)
        self.assertEqual(config.read_bytes(), contents)
        self.assertEqual(wrapper.read_bytes(), before)
        parsed = update.load_settings(config)
        self.assertEqual(parsed.repository, update.PUBLIC_REPOSITORY)
        subprocess.run(["sh", "-n", str(wrapper)], check=True)
        wrapper.write_text("#!/bin/sh\n# personal command\n")
        with self.assertRaisesRegex(update.UpdateError, "unmanaged"):
            update.setup(self.repo, self.home, Path(sys.executable))

    def test_symlinked_state_or_config_is_refused(self) -> None:
        self.settings.state.parent.mkdir(parents=True, exist_ok=True)
        outside = self.base / "outside"
        outside.mkdir()
        self.settings.state.symlink_to(outside)
        with self.assertRaises(install.InstallError):
            self.updater.run()
        self.assertFalse(list(outside.iterdir()))

    def test_interrupted_installed_transaction_recovers_receipt_and_links(self) -> None:
        self.advance()
        with patch.object(self.updater, "verify_live", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        self.assertEqual(self.updater.run()["result"], "recovered")
        self.assert_current(self.previous)

    def test_partial_link_failure_rolls_back_installer_and_source(self) -> None:
        self.advance()
        original = os.link
        failed = False

        def fail_once(source: Path, destination: Path) -> None:
            nonlocal failed
            if Path(destination).parent == self.settings.codex_home / "agents" and not failed:
                failed = True
                raise OSError("Injected live hardlink failure")
            original(source, destination)

        with patch.object(install.os, "link", side_effect=fail_once):
            result = self.updater.run()
        self.assertTrue(failed)
        self.assertEqual(result["result"], "rolled-back", result)
        self.assert_current(self.previous)

    def test_cli_status_reads_without_mutation(self) -> None:
        result = self.updater.run()
        config = self.base / "config.json"
        update.atomic_json(
            config,
            {
                "schema": update.SCHEMA,
                "repository": update.PUBLIC_REPOSITORY,
                "branch": "main",
                "source": str(self.repo),
                "home": str(self.home),
                "codex_home": str(self.settings.codex_home),
                "validation_python": sys.executable,
            },
        )
        self.assertEqual(update.main(["--config", str(config), "status"]), 0)
        self.assertEqual(update.read_json(self.settings.state / "latest.json"), result)

    def test_missing_required_gate_is_not_an_empty_passing_test_run(self) -> None:
        with self.assertRaisesRegex(update.UpdateError, "required deployment test"):
            update.Updater(self.settings).deployment_checks(self.repo)

    def test_candidate_revision_change_blocks_promotion(self) -> None:
        self.advance()
        original = self.updater.validate_candidate

        def change_revision(candidate: Path, run: Path) -> list[dict[str, object]]:
            checks = original(candidate, run)
            update.git(candidate, "checkout", "--detach", self.previous)
            return checks

        with patch.object(self.updater, "validate_candidate", side_effect=change_revision):
            result = self.updater.run()
        self.assertEqual(result["result"], "failed-validation", result)
        self.assert_current(self.previous)

    def test_new_skill_is_added_and_removed_by_rollback(self) -> None:
        skill = self.upstream / "skills/new-example-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: new-example-skill\ndescription: Fixture.\n---\nExample.\n"
        )
        target = self.commit(self.upstream, "fixture new skill")
        result = self.updater.run()
        self.assertEqual(result["result"], "updated", result)
        self.assert_current(target)
        installed = self.home / ".agents/skills/new-example-skill"
        self.assertTrue(installed.is_symlink())
        result = self.updater.run(rollback=True)
        self.assertEqual(result["result"], "rollback-complete", result)
        self.assertFalse(installed.is_symlink())
        self.assert_current(self.previous)

    def test_recovery_preserves_foreign_destination(self) -> None:
        self.advance()
        with patch.object(self.updater, "verify_live", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        role = self.settings.codex_home / "agents/documentation-agent.toml"
        temporary = role.with_suffix(".new")
        temporary.write_text("personal role replacement")
        temporary.replace(role)
        result = self.updater.run()
        self.assertEqual(result["result"], "recovery-required", result)
        self.assertEqual(role.read_text(), "personal role replacement")

    def test_removed_standalone_skill_holds_before_validation(self) -> None:
        shutil.rmtree(self.upstream / "skills/release-and-docs-skill")
        self.commit(self.upstream, "fixture removal")
        with patch.object(self.updater, "validate_candidate") as validate:
            result = self.updater.run()
        self.assertEqual(result["result"], "blocked-layout-change", result)
        validate.assert_not_called()
        self.assert_current(self.previous)
        self.assertTrue((self.home / ".agents/skills/release-and-docs-skill").is_dir())

    def test_registry_detects_retired_skill_after_external_source_update(self) -> None:
        self.assertEqual(self.updater.run()["result"], "current")
        backup = self.settings.state / "reviewed-retirement"
        backup.mkdir()
        shutil.copytree(self.repo / "skills/release-and-docs-skill", backup / "source-package")
        shutil.rmtree(self.upstream / "skills/release-and-docs-skill")
        target = self.commit(self.upstream, "fixture external retirement")
        update.git(self.repo, "fetch", "origin")
        update.git(self.repo, "merge", "--ff-only", target)
        stale = self.home / ".agents/skills/release-and-docs-skill"
        self.assertTrue(stale.is_symlink())
        self.assertFalse(stale.exists())
        result = self.updater.run()
        self.assertEqual(result["result"], "blocked-layout-change", result)
        stale.rename(backup / "installed-link")
        self.assertTrue((backup / "source-package/SKILL.md").is_file())
        self.assertTrue((backup / "installed-link").is_symlink())
        self.assertEqual(self.updater.run()["result"], "current")

    def test_saved_retired_role_survives_runtime_refresh_as_a_hold(self) -> None:
        self.assertEqual(self.updater.run()["result"], "current")
        registry = self.settings.state / "managed.json"
        data = update.read_json(registry)
        retired = self.settings.codex_home / "agents/retired-example-agent.toml"
        os.link(self.repo / "agents/codex/documentation-agent.toml", retired)
        data["entries"].append(str(retired))
        update.atomic_json(registry, data)
        result = self.updater.run()
        self.assertEqual(result["result"], "blocked-layout-change", result)
        with self.assertRaisesRegex(update.UpdateError, "outside the catalog"):
            update.setup(self.repo, self.home, Path(sys.executable))
        self.assertTrue(retired.is_file())

    def test_rolled_back_revision_stays_held_until_explicit_retry(self) -> None:
        self.advance()
        self.assertEqual(self.updater.run()["result"], "updated")
        self.assertEqual(self.updater.run(rollback=True)["result"], "rollback-complete")
        self.assertEqual(self.updater.run()["result"], "blocked-rolled-back")
        self.assert_current(self.previous)
        self.assertEqual(self.updater.run(retry_rolled_back=True)["result"], "updated")

    def test_recovery_refuses_other_profile_receipt_without_retiring_its_skill(self) -> None:
        skill = self.upstream / "skills/new-example-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: new-example-skill\ndescription: Fixture.\n---\nExample.\n"
        )
        self.advance()
        original = self.updater.install_from

        def interrupt_live(
            root: Path, home: Path, codex: Path, log: Path, *, receipt_id: str | None = None
        ) -> Path | None:
            if home == self.home:
                raise KeyboardInterrupt
            return original(root, home, codex, log, receipt_id=receipt_id)

        with patch.object(self.updater, "install_from", side_effect=interrupt_live):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        install.install(
            self.repo,
            "codex",
            ["new-example-skill"],
            self.home,
            self.home / ".codex-other",
            backup_existing=False,
            dry_run=False,
            preserve_legacy_skills=("doc-agent",),
        )
        destination = self.home / ".agents/skills/new-example-skill"
        before = update.fingerprint(destination)
        result = self.updater.run()
        self.assertEqual(result["result"], "recovery-required", result)
        self.assertEqual(update.fingerprint(destination), before)

    def interrupt_before_live_install(self) -> None:
        original = self.updater.install_from

        def interrupt(
            root: Path, home: Path, codex: Path, log: Path, **kwargs: object
        ) -> Path | None:
            if home == self.home:
                raise KeyboardInterrupt
            return original(root, home, codex, log, **kwargs)

        with patch.object(self.updater, "install_from", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()

    def test_same_profile_manual_receipt_is_never_adopted_for_recovery(self) -> None:
        skill = self.upstream / "skills/new-example-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: new-example-skill\ndescription: Fixture.\n---\nExample.\n"
        )
        target = self.advance()
        self.interrupt_before_live_install()
        receipt = install.install(
            self.repo,
            "codex",
            ["new-example-skill"],
            self.home,
            self.settings.codex_home,
            backup_existing=False,
            dry_run=False,
            preserve_legacy_skills=("doc-agent",),
        )
        assert receipt is not None
        before = receipt.read_bytes()
        destination = self.home / ".agents/skills/new-example-skill"
        result = self.updater.run()
        self.assertEqual(result["result"], "recovery-required", result)
        self.assertTrue(destination.is_symlink())
        self.assertEqual(receipt.read_bytes(), before)
        self.assertEqual(update.git(self.repo, "rev-parse", "HEAD"), target)

    def test_own_and_foreign_same_profile_receipts_hold_before_restoring_either(self) -> None:
        self.advance()
        with patch.object(self.updater, "verify_live", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        transaction = update.read_json(self.settings.state / "transaction.json")
        own = Path(transaction["receipt"])
        role = self.settings.codex_home / "agents/documentation-agent.toml"
        temporary = role.with_suffix(".copy")
        temporary.write_bytes(role.read_bytes())
        temporary.replace(role)
        manual = install.install(
            self.repo,
            "codex",
            ["documentation-skill"],
            self.home,
            self.settings.codex_home,
            backup_existing=True,
            dry_run=False,
            preserve_legacy_skills=("doc-agent",),
        )
        assert manual is not None
        before = {path: path.read_bytes() for path in (own, manual)}
        result = self.updater.run()
        self.assertEqual(result["result"], "recovery-required", result)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_owned_receipt_is_known_before_installer_returns(self) -> None:
        self.advance()
        original = self.updater.install_from

        def finish_then_interrupt(
            root: Path, home: Path, codex: Path, log: Path, **kwargs: object
        ) -> Path | None:
            receipt = original(root, home, codex, log, **kwargs)
            if home == self.home:
                raise KeyboardInterrupt
            return receipt

        with patch.object(self.updater, "install_from", side_effect=finish_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        transaction = update.read_json(self.settings.state / "transaction.json")
        own = update.read_json(Path(transaction["receipt"]))
        self.assertEqual(own["operation_id"], transaction["operation_id"])
        self.assertEqual(self.updater.run()["result"], "recovered")
        self.assert_current(self.previous)

    def test_pending_owned_receipt_is_identified_without_guessing_partial_writes(self) -> None:
        self.advance()
        original = os.link

        def interrupt(source: Path, destination: Path) -> None:
            if Path(destination).parent == self.settings.codex_home / "agents":
                raise KeyboardInterrupt
            original(source, destination)

        with patch.object(install.os, "link", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        transaction = update.read_json(self.settings.state / "transaction.json")
        receipt = Path(transaction["receipt"])
        self.assertEqual(update.read_json(receipt)["state"], "pending")
        before = receipt.read_bytes()
        self.assertEqual(self.updater.run()["result"], "recovery-required")
        self.assertEqual(receipt.read_bytes(), before)

    def test_missing_or_mismatched_owned_receipt_holds(self) -> None:
        self.advance()
        with patch.object(self.updater, "verify_live", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        transaction = update.read_json(self.settings.state / "transaction.json")
        receipt = Path(transaction["receipt"])
        data = update.read_json(receipt)
        changed = {**data, "operation_id": "unrelated-operation"}
        update.atomic_json(receipt, changed)
        self.assertEqual(self.updater.run()["result"], "recovery-required")
        update.atomic_json(receipt, data)
        receipt.rename(receipt.with_suffix(".saved"))
        self.assertEqual(self.updater.run()["result"], "recovery-required")

    def test_repair_receipt_is_owned_before_return_and_recovery_is_resumable(self) -> None:
        self.advance()
        original = self.updater.install_from
        verify = self.updater.verify_live
        failed = False

        def fail_initial(preserved: dict[str, object]) -> list[dict[str, str]]:
            nonlocal failed
            if not failed:
                failed = True
                raise update.UpdateError("failed-verification", "Injected initial failure")
            return verify(preserved)

        def interrupt_repair(
            root: Path, home: Path, codex: Path, log: Path, **kwargs: object
        ) -> Path | None:
            receipt = original(root, home, codex, log, **kwargs)
            if str(kwargs.get("receipt_id", "")).endswith("-repair"):
                raise KeyboardInterrupt
            return receipt

        with (
            patch.object(self.updater, "verify_live", side_effect=fail_initial),
            patch.object(self.updater, "install_from", side_effect=interrupt_repair),
        ):
            with self.assertRaises(KeyboardInterrupt):
                self.updater.run()
        transaction = update.read_json(self.settings.state / "transaction.json")
        repair = update.read_json(Path(transaction["recovery_receipt"]))
        self.assertEqual(repair["operation_id"], transaction["operation_id"] + "-repair")
        self.assertEqual(self.updater.run()["result"], "recovered")
        self.assert_current(self.previous)


if __name__ == "__main__":
    unittest.main()
