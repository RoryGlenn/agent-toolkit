#!/usr/bin/env python3
"""Check and deploy public Toolkit main without discarding local work."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import install

PUBLIC_REPOSITORY = "https://github.com/RoryGlenn/agent-toolkit.git"
SCHEMA = "agent-toolkit-update/v1"
RUNTIME_FILES = ("toolkit_update.py", "install.py", "project_bootstrap.py")
CLOSED_PHASES = {"complete", "rolled-back", "cancelled"}
TEST_FILES = (
    "test_install.py",
    "test_routing.py",
    "test_project_bootstrap.py",
    "test_project_reconfiguration.py",
    "test_toolkit_update.py",
)


class UpdateError(ValueError):
    """A held or failed operation with a stable status code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Settings:
    """Explicit paths; no inherited CODEX_HOME or configurable shell commands."""

    source: Path
    home: Path
    codex_home: Path
    validation_python: Path
    repository: str = PUBLIC_REPOSITORY
    branch: str = "main"

    @property
    def state(self) -> Path:
        return self.home / ".local/state/agent-toolkit/updates"

    @property
    def candidates(self) -> Path:
        return self.home / "repos/.agent-toolkit-update-candidates"


def atomic_json(path: Path, value: Any) -> None:
    """Persist private state without following an existing destination link."""
    install.check_parents(path.parent)
    if path.is_symlink():
        raise UpdateError("unsafe-path", f"Inspect linked state file: {path}")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    """Read one direct JSON object, refusing aliases."""
    install.check_parents(path.parent)
    if path.is_symlink() or not path.is_file():
        raise UpdateError("unsafe-path", f"Expected a direct JSON file: {path}")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise UpdateError("invalid-state", f"Expected a JSON object: {path}")
    return value


def fingerprint(path: Path) -> dict[str, Any]:
    """Describe identity and bytes without following a directory symlink."""
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "missing"}
    if path.is_file():
        info = path.stat()
        return {
            "kind": "file",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "device": info.st_dev,
            "inode": info.st_ino,
        }
    if path.is_dir():
        return {
            "kind": "directory",
            "entries": {p.name: fingerprint(p) for p in sorted(path.iterdir())},
        }
    raise UpdateError("unsafe-path", f"Unexpected special file: {path}")


def git(root: Path, *arguments: str) -> str:
    """Run bounded Git without hooks, prompting or ambient credential helpers."""
    environment = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
    }
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=", *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode:
        raise UpdateError("git-failed", result.stderr.strip() or "Git command failed.")
    return result.stdout.strip()


class Updater:
    """Own preflight, candidate checks, deployment and guarded recovery."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def source_guard(self, expected_head: str | None = None) -> str:
        """Require a retained direct checkout on the expected clean branch."""
        cfg = self.settings
        if git(cfg.source, "rev-parse", "--show-toplevel") != str(cfg.source):
            raise UpdateError("wrong-source", "Configured source is not the Git root.")
        if git(cfg.source, "symbolic-ref", "--short", "HEAD") != cfg.branch:
            raise UpdateError("wrong-branch", f"Expected branch {cfg.branch}.")
        if git(cfg.source, "remote", "get-url", "origin") != cfg.repository:
            raise UpdateError(
                "wrong-repository", "Origin does not match the approved public source."
            )
        if any(line[:1] != "H" for line in git(cfg.source, "ls-files", "-v").splitlines()):
            raise UpdateError(
                "blocked-index-flags", "Inspect sparse or assume-unchanged index entries."
            )
        if git(cfg.source, "status", "--porcelain=v1", "--untracked-files=all"):
            raise UpdateError(
                "blocked-local-changes",
                "Unpublished local changes are preserved. Reconcile them before deployment.",
            )
        head = git(cfg.source, "rev-parse", "HEAD")
        if expected_head is not None and head != expected_head:
            raise UpdateError("source-changed", "Source HEAD changed during this operation.")
        return head

    def entries(self, root: Path) -> list[dict[str, str]]:
        cfg = self.settings
        return install.installation_status(
            root, "codex", list(install.inventory(root)), cfg.home, cfg.codex_home
        )

    def managed_snapshot(self) -> dict[str, Any]:
        """Require current ownership; status alone never grants replacement rights."""
        cfg = self.settings
        entries = self.entries(cfg.source)
        if not entries or any(item["state"] != "current" for item in entries):
            raise UpdateError(
                "blocked-installation", "Inspect missing or different global entries."
            )
        paths = install.locations(cfg.home, cfg.codex_home)
        return {
            str(paths[item["area"]] / item["name"]): fingerprint(paths[item["area"]] / item["name"])
            for item in entries
        }

    def preserved_snapshot(self) -> dict[str, Any]:
        cfg = self.settings
        return {
            str(path): fingerprint(path)
            for path in (
                cfg.codex_home / "skills/doc-agent",
                cfg.home / ".agents/skills/doc-agent",
                cfg.codex_home / "AGENTS.md",
            )
        }

    def registry_guard(self, snapshot: dict[str, Any]) -> None:
        """Keep retired owned paths visible across reviewed runtime refreshes."""
        cfg = self.settings
        path = cfg.state / "managed.json"
        if not path.exists():
            self.save_registry(snapshot)
            return
        data = read_json(path)
        if (
            data.get("schema") != SCHEMA
            or data.get("source") != str(cfg.source)
            or data.get("home") != str(cfg.home)
            or data.get("codex_home") != str(cfg.codex_home)
            or not isinstance(data.get("entries"), list)
            or any(not isinstance(entry, str) for entry in data["entries"])
        ):
            raise UpdateError(
                "invalid-registry", "Inspect the saved installation ownership registry."
            )
        retired = set(data["entries"]) - snapshot.keys()
        directories = {cfg.home / ".agents/skills", cfg.codex_home / "agents"}
        for entry in data["entries"]:
            if Path(entry).parent not in directories:
                raise UpdateError(
                    "invalid-registry", "A saved managed path is outside this profile."
                )
            install.check_parents(Path(entry).parent)
        remaining = sorted(entry for entry in retired if install.present(Path(entry)))
        if remaining:
            raise UpdateError(
                "blocked-layout-change",
                "Previously managed entries remain outside the catalog:\n" + "\n".join(remaining),
            )

    def save_registry(self, snapshot: dict[str, Any]) -> None:
        cfg = self.settings
        install.check_parents(cfg.state)
        cfg.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic_json(
            cfg.state / "managed.json",
            {
                "schema": SCHEMA,
                "source": str(cfg.source),
                "home": str(cfg.home),
                "codex_home": str(cfg.codex_home),
                "entries": sorted(snapshot),
            },
        )

    def install_from(
        self, root: Path, home: Path, codex: Path, log: Path, *, receipt_id: str | None = None
    ) -> Path | None:
        with log.open("a") as output, contextlib.redirect_stdout(output):
            return install.install(
                root,
                "codex",
                list(install.inventory(root)),
                home,
                codex,
                backup_existing=True,
                dry_run=False,
                preserve_legacy_skills=("doc-agent",),
                receipt_id=receipt_id,
            )

    def deployment_checks(self, candidate: Path) -> list[list[str]]:
        """Fixed bounded gates; do not install dependencies or run a model."""
        if any(not (candidate / "tests" / name).is_file() for name in TEST_FILES):
            raise UpdateError("failed-validation", "A required deployment test file is missing.")
        python = str(self.settings.validation_python)
        commands = [[python, "install.py", "check"], [python, "authoring.py", "check"]]
        commands.extend(
            [python, "-m", "unittest", "discover", "-s", "tests", "-p", name] for name in TEST_FILES
        )
        if (candidate / "tests/test_usage_audit.py").is_file():
            commands.append(
                [python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_usage_audit.py"]
            )
        return commands + [
            [python, "-m", "ruff", "check", "."],
            [python, "-m", "ruff", "format", "--check", "."],
            [python, "-m", "mypy"],
        ]

    def validate_candidate(self, candidate: Path, run: Path) -> list[dict[str, Any]]:
        """Check a detached revision and exercise install/status/restore privately."""
        install.inventory(candidate)  # A changed role mapping requires a runtime review.
        home = run / "test-home"
        standalone = home / ".codex/skills/doc-agent/SKILL.md"
        standalone.parent.mkdir(parents=True)
        standalone.write_text("Independent Doc Agent preservation canary.\n")
        before = fingerprint(standalone)
        receipt = self.install_from(candidate, home, home / ".codex", run / "checks.log")
        entries = install.installation_status(
            candidate, "codex", list(install.inventory(candidate)), home, home / ".codex"
        )
        if any(item["state"] != "current" for item in entries) or before != fingerprint(standalone):
            raise UpdateError("failed-validation", "Isolated installation verification failed.")
        assert receipt is not None
        with (run / "checks.log").open("a") as output, contextlib.redirect_stdout(output):
            install.restore(receipt)
        if before != fingerprint(standalone):
            raise UpdateError("failed-validation", "Isolated restore changed the Doc Agent.")
        checks = []
        for command in self.deployment_checks(candidate):
            with (run / "checks.log").open("a") as output:
                output.write("\n$ " + shlex.join(command) + "\n")
                output.flush()
                result = subprocess.run(
                    command,
                    cwd=candidate,
                    env={
                        "PATH": os.defpath,
                        "LANG": "C.UTF-8",
                        "HOME": str(home),
                        "XDG_CONFIG_HOME": str(home / ".config"),
                        "XDG_STATE_HOME": str(home / ".local/state"),
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    timeout=300,
                )
            checks.append({"command": command, "exit_code": result.returncode})
            atomic_json(run / "checks.json", {"checks": checks})
            if result.returncode:
                raise UpdateError(
                    "failed-validation", f"Deployment check failed: {shlex.join(command)}"
                )
        if git(candidate, "status", "--porcelain=v1", "--untracked-files=all"):
            raise UpdateError("failed-validation", "Candidate checks left source modifications.")
        return checks

    def preflight_plan(self, candidate: Path, before: dict[str, Any]) -> None:
        """A planned replacement must already belong to this exact installation."""
        cfg = self.settings
        paths = install.locations(cfg.home, cfg.codex_home)
        candidate_paths = {
            str(paths[item["area"]] / item["name"]) for item in self.entries(candidate)
        }
        retired = sorted(before.keys() - candidate_paths)
        if retired:
            raise UpdateError(
                "blocked-layout-change",
                "Candidate removes managed entries; review this migration:\n" + "\n".join(retired),
            )
        entries = install.plan_install(
            candidate,
            "codex",
            list(install.inventory(candidate)),
            paths,
            backup_existing=True,
            preserve_legacy_skills=("doc-agent",),
        )
        for item in entries:
            destination = paths[item.area] / item.name
            if install.present(destination) and str(destination) not in before:
                raise UpdateError("blocked-installation", f"Unmanaged collision: {destination}")

    def verify_live(self, preserved: dict[str, Any]) -> list[dict[str, str]]:
        cfg = self.settings
        entries = self.entries(cfg.source)
        if any(item["state"] != "current" for item in entries):
            raise UpdateError("failed-verification", "Updated global links are not all current.")
        if preserved != self.preserved_snapshot():
            raise UpdateError("failed-verification", "Preserved workflow or guidance changed.")
        return entries

    def receipts(self) -> set[str]:
        directory = self.settings.home / ".local/state/agent-toolkit/installations"
        install.check_parents(directory)
        return {str(path) for path in directory.glob("*/receipt.json")}

    def recover(self, transaction: dict[str, Any], run: Path) -> None:
        """Recover only the exact known transaction; preserve unexpected edits."""
        try:
            self._recover(transaction, run)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise UpdateError("recovery-required", f"Recovery stopped: {error}") from error

    def _recover(self, transaction: dict[str, Any], run: Path) -> None:
        """Restore receipt before source, then repair canonical role inodes."""
        cfg = self.settings
        try:
            head = self.source_guard()
        except UpdateError as error:
            raise UpdateError("recovery-required", f"Recovery held: {error}") from error
        if head not in {transaction["previous"], transaction["candidate"]}:
            raise UpdateError("recovery-required", "HEAD differs from both transaction revisions.")
        if transaction["preserved"] != self.preserved_snapshot():
            raise UpdateError("recovery-required", "Preserved workflow changed after preflight.")
        operation_id = transaction.get("operation_id")
        if not isinstance(operation_id, str) or not install.NAME.fullmatch(operation_id.lower()):
            raise UpdateError("recovery-required", "Transaction has no valid owned operation ID.")
        storage = cfg.home / ".local/state/agent-toolkit/installations"
        primary = storage / operation_id / "receipt.json"
        repair_id = operation_id + "-repair"
        repair = storage / repair_id / "receipt.json"
        if transaction.get("receipt") != str(primary) or transaction.get("recovery_receipt") != str(
            repair
        ):
            raise UpdateError(
                "recovery-required", "Transaction receipt paths do not match its IDs."
            )
        for receipt_name in self.receipts() - set(transaction["prior_receipts"]):
            data = read_json(Path(receipt_name))
            if data.get("source") == str(cfg.source) and receipt_name not in {
                str(primary),
                str(repair),
            }:
                raise UpdateError(
                    "recovery-required", "Another installation created an unowned receipt."
                )
        owned: dict[Path, dict[str, Any]] = {}
        for path, identity in ((primary, operation_id), (repair, repair_id)):
            if not install.present(path):
                continue
            data = read_json(path)
            if (
                data.get("schema") != install.SCHEMA
                or data.get("operation_id") != identity
                or data.get("source") != str(cfg.source)
                or data.get("home") != str(cfg.home)
                or data.get("codex_home") != str(cfg.codex_home)
            ):
                raise UpdateError(
                    "recovery-required", "Owned receipt identity does not match the transaction."
                )
            if data.get("state") not in {"installed", "restored"}:
                raise UpdateError(
                    "recovery-required", f"Inspect incomplete installation receipt: {path}"
                )
            owned[path] = data
        if primary not in owned and transaction.get("receipt_created"):
            raise UpdateError(
                "recovery-required", "Required owned installation receipt is missing."
            )
        if repair in owned:
            if head != transaction["previous"] or owned[repair]["state"] != "installed":
                raise UpdateError(
                    "recovery-required", "Repair receipt is in an unexpected source state."
                )
            self.verify_live(transaction["preserved"])
            self.save_registry(self.managed_snapshot())
            transaction["phase"] = "rolled-back"
            atomic_json(cfg.state / "transaction.json", transaction)
            return
        if primary in owned and owned[primary]["state"] == "installed":
            with (run / "recovery.log").open("a") as output, contextlib.redirect_stdout(output):
                install.restore(primary)
        # Restored agent inodes may be detached from HEAD; exact preflight identity
        # prevents recovery from overwriting a subsequent personal replacement.
        for path, expected in transaction["before"].items():
            if fingerprint(Path(path)) != expected:
                raise UpdateError("recovery-required", f"Destination changed: {path}")
        if head == transaction["candidate"]:
            # Removing installed hardlinks changes source ctime. Refresh Git's stat
            # cache before reset --keep, which otherwise can reject unchanged files.
            self.source_guard(head)
            git(cfg.source, "update-index", "--refresh")
            git(cfg.source, "reset", "--keep", transaction["previous"])
        transaction["phase"] = "repairing"
        atomic_json(cfg.state / "transaction.json", transaction)
        receipt = self.install_from(
            cfg.source, cfg.home, cfg.codex_home, run / "recovery.log", receipt_id=repair_id
        )
        self.verify_live(transaction["preserved"])
        self.save_registry(self.managed_snapshot())
        transaction.update(phase="rolled-back", recovery_receipt_created=receipt is not None)
        atomic_json(cfg.state / "transaction.json", transaction)

    def execute(self, run: Path, *, retry_rolled_back: bool = False) -> dict[str, Any]:
        """Validate before the first live mutation and journal promotion."""
        cfg = self.settings
        transaction_path = cfg.state / "transaction.json"
        pending: dict[str, Any] = {}
        if transaction_path.exists():
            pending = read_json(transaction_path)
            if pending.get("phase") not in CLOSED_PHASES:
                self.recover(pending, run)
                return {"result": "recovered", "previous": pending["previous"]}
        previous = self.source_guard()
        before = self.managed_snapshot()
        self.registry_guard(before)
        preserved = self.preserved_snapshot()
        if shutil.disk_usage(cfg.source).free < 512 * 1024 * 1024:
            raise UpdateError("insufficient-disk", "At least 512 MiB free disk is required.")
        git(
            cfg.source,
            "fetch",
            "--no-tags",
            cfg.repository,
            f"+refs/heads/{cfg.branch}:refs/agent-toolkit-updater/candidate",
        )
        candidate_sha = git(cfg.source, "rev-parse", "refs/agent-toolkit-updater/candidate")
        if previous == candidate_sha:
            self.save_registry(before)
            return {"result": "current", "installed_revision": previous, "entries": len(before)}
        if (
            pending.get("phase") == "rolled-back"
            and pending.get("candidate") == candidate_sha
            and not retry_rolled_back
        ):
            raise UpdateError(
                "blocked-rolled-back",
                "Revision was rolled back. Review it before using run --retry-rolled-back.",
            )
        try:
            git(cfg.source, "merge-base", "--is-ancestor", previous, candidate_sha)
        except UpdateError as error:
            raise UpdateError(
                "blocked-history", "Public main is not a fast-forward of this checkout."
            ) from error
        candidate = cfg.candidates / run.name / "source"
        install.check_parents(candidate.parent)
        candidate.parent.mkdir(parents=True, mode=0o700)
        git(cfg.source, "worktree", "add", "--detach", str(candidate), candidate_sha)
        self.preflight_plan(candidate, before)
        checks = self.validate_candidate(candidate, run)
        if git(candidate, "rev-parse", "HEAD") != candidate_sha or any(
            line[:1] != "H" for line in git(candidate, "ls-files", "-v").splitlines()
        ):
            raise UpdateError("failed-validation", "Candidate revision or index flags changed.")
        self.source_guard(previous)
        if before != self.managed_snapshot() or preserved != self.preserved_snapshot():
            raise UpdateError("installation-changed", "Installation changed during validation.")
        self.preflight_plan(candidate, before)
        operation_id = "update-" + run.name
        storage = cfg.home / ".local/state/agent-toolkit/installations"
        transaction: dict[str, Any] = {
            "schema": SCHEMA,
            "phase": "prepared",
            "previous": previous,
            "candidate": candidate_sha,
            "candidate_path": str(candidate),
            "before": before,
            "preserved": preserved,
            "prior_receipts": sorted(self.receipts()),
            "operation_id": operation_id,
            "receipt": str(storage / operation_id / "receipt.json"),
            "recovery_receipt": str(storage / (operation_id + "-repair") / "receipt.json"),
            "run": str(run),
        }
        atomic_json(transaction_path, transaction)
        try:
            git(cfg.source, "merge", "--ff-only", "--no-edit", candidate_sha)
            transaction["phase"] = "promoted"
            atomic_json(transaction_path, transaction)
            if any(fingerprint(Path(path)) != value for path, value in before.items()):
                raise UpdateError("installation-changed", "Destination changed before refresh.")
            receipt = self.install_from(
                cfg.source, cfg.home, cfg.codex_home, run / "install.log", receipt_id=operation_id
            )
            transaction.update(phase="installed", receipt_created=receipt is not None)
            atomic_json(transaction_path, transaction)
            entries = self.verify_live(preserved)
            self.source_guard(candidate_sha)
            self.save_registry(self.managed_snapshot())
            transaction["phase"] = "complete"
            atomic_json(transaction_path, transaction)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            try:
                self.recover(transaction, run)
            except (OSError, ValueError, subprocess.SubprocessError) as recovery_error:
                raise UpdateError(
                    "recovery-required",
                    f"Deployment failed: {error}; recovery stopped: {recovery_error}",
                ) from recovery_error
            raise UpdateError(
                "rolled-back", f"Deployment failed and prior source was restored: {error}"
            ) from error
        return {
            "result": "updated",
            "previous": previous,
            "installed_revision": candidate_sha,
            "entries": len(entries),
            "checks": checks,
            "receipt": transaction["receipt"] if receipt is not None else None,
            "discovery": "structural-role-validation; start a fresh Codex session",
        }

    def run(self, *, rollback: bool = False, retry_rolled_back: bool = False) -> dict[str, Any]:
        """Run once with exclusive state ownership and a private result record."""
        cfg = self.settings
        for path in (cfg.source, cfg.home, cfg.codex_home, cfg.state, cfg.candidates):
            install.check_parents(path)
        cfg.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(
            cfg.state / "update.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return {
                    "schema": SCHEMA,
                    "result": "busy",
                    "message": "Another updater holds the lock.",
                }
            run = (
                cfg.state
                / "runs"
                / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:10])
            )
            install.check_parents(run)
            run.mkdir(parents=True, mode=0o700)
            result: dict[str, Any] = {
                "schema": SCHEMA,
                "started_at": datetime.now(UTC).isoformat(),
                "source": str(cfg.source),
                "evidence": str(run),
            }
            try:
                if rollback:
                    transaction = read_json(cfg.state / "transaction.json")
                    if transaction.get("phase") != "complete":
                        raise UpdateError(
                            "no-update-to-rollback", "No completed update is available."
                        )
                    self.recover(transaction, run)
                    result.update(
                        result="rollback-complete", installed_revision=transaction["previous"]
                    )
                else:
                    result.update(self.execute(run, retry_rolled_back=retry_rolled_back))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                result.update(
                    result=error.code if isinstance(error, UpdateError) else "failed",
                    message=str(error),
                )
            result["finished_at"] = datetime.now(UTC).isoformat()
            candidate = cfg.candidates / run.name / "source"
            if candidate.exists():
                result["candidate_path"] = str(candidate)
            result["managed_registry"] = str(cfg.state / "managed.json")
            atomic_json(run / "result.json", result)
            atomic_json(cfg.state / "latest.json", result)
            return result


def setup(source: Path, home: Path, python: Path) -> Path:
    """Save a fixed reviewed runtime and units; enabling the timer is separate."""
    for path in (source, home, home / ".config/systemd/user", home / ".local/bin"):
        install.check_parents(path)
    if not python.is_absolute() or not python.is_file():
        raise UpdateError("missing-python", "Supply the existing development Python interpreter.")
    if not source.is_relative_to(home / "repos") or not source.is_dir():
        raise UpdateError(
            "wrong-source", "Keep the retained checkout under the target home's repos directory."
        )
    settings = Settings(source, home, home / ".codex", python)
    transaction = settings.state / "transaction.json"
    if transaction.exists() and read_json(transaction).get("phase") not in CLOSED_PHASES:
        raise UpdateError(
            "recovery-required", "Finish the existing transaction before runtime setup."
        )
    updater = Updater(settings)
    updater.registry_guard(updater.managed_snapshot())
    for name in RUNTIME_FILES:
        if (source / name).is_symlink() or not (source / name).is_file():
            raise UpdateError("unsafe-path", f"Expected reviewed runtime source: {name}")
    digest = hashlib.sha256(
        b"".join((source / name).read_bytes() for name in RUNTIME_FILES)
    ).hexdigest()
    runtime = home / ".local/lib/agent-toolkit-updater" / digest[:20]
    install.check_parents(runtime)
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name in RUNTIME_FILES:
        target = runtime / name
        runtime_bytes = (source / name).read_bytes()
        if target.is_symlink() or (target.exists() and target.read_bytes() != runtime_bytes):
            raise UpdateError("runtime-changed", f"Inspect changed fixed runtime: {target}")
        if not target.exists():
            target.write_bytes(runtime_bytes)
            target.chmod(0o600)
    command = home / ".local/bin/agent-toolkit-update"
    config = home / ".config/agent-toolkit/update.json"
    install.check_parents(config.parent)
    if config.exists() and read_json(config).get("schema") != SCHEMA:
        raise UpdateError("unmanaged-file", f"Inspect existing configuration: {config}")
    marker = "# Managed by agent-toolkit-updater\n"
    wrapper = (
        "#!/bin/sh\n"
        + marker
        + "exec "
        + shlex.join([sys.executable, str(runtime / "toolkit_update.py"), "--config", str(config)])
        + ' "$@"\n'
    )
    files = {command: wrapper}
    units = source / "systemd"
    for name in ("agent-toolkit-update.service", "agent-toolkit-update.timer"):
        text = (units / name).read_text()
        files[home / ".config/systemd/user" / name] = text.replace(
            "@COMMAND@", json.dumps(str(command), ensure_ascii=False).replace("%", "%%")
        )
    for path in files:
        install.check_parents(path.parent)
        if path.is_symlink() or (path.exists() and marker.strip() not in path.read_text()):
            raise UpdateError("unmanaged-file", f"Inspect existing unmanaged setup file: {path}")
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text() == content:
            continue
        if path.exists():
            backup = home / ".local/state/agent-toolkit/updates/setup-backups" / uuid.uuid4().hex
            install.check_parents(backup)
            backup.mkdir(parents=True, mode=0o700)
            shutil.copy2(path, backup / path.name)
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.write_text(content)
            temporary.chmod(0o700 if path == command else 0o600)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    command.chmod(0o700)
    config.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "schema": SCHEMA,
        **{key: str(value) for key, value in asdict(settings).items()},
        "runtime_sha256": digest,
    }
    if config.exists() and read_json(config) != value:
        backup = settings.state / "setup-backups" / uuid.uuid4().hex
        install.check_parents(backup)
        backup.mkdir(parents=True, mode=0o700)
        shutil.copy2(config, backup / "update.json")
    atomic_json(config, value)
    return config


def load_settings(config: Path) -> Settings:
    value = read_json(config)
    if (
        value.get("schema") != SCHEMA
        or value.get("repository") != PUBLIC_REPOSITORY
        or value.get("branch") != "main"
    ):
        raise UpdateError("invalid-config", "Use the approved public repository and main branch.")
    paths = {
        name: Path(value[name]) for name in ("source", "home", "codex_home", "validation_python")
    }
    if any(
        not path.is_absolute() or ".." in path.parts or any(c in str(path) for c in "\n\r\0")
        for path in paths.values()
    ) or paths["home"] == Path("/"):
        raise UpdateError(
            "invalid-config", "Configuration paths must be absolute without parent components."
        )
    if not paths["source"].is_relative_to(paths["home"] / "repos"):
        raise UpdateError(
            "invalid-config", "Keep retained source under the configured home's repos directory."
        )
    return Settings(paths["source"], paths["home"], paths["codex_home"], paths["validation_python"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path.home() / ".config/agent-toolkit/update.json"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser(
        "setup", help="Save reviewed runtime and units without enabling them."
    )
    configure.add_argument("--source", type=Path, required=True)
    configure.add_argument("--home", type=Path, default=Path.home())
    configure.add_argument("--validation-python", type=Path, required=True)
    run = commands.add_parser(
        "run", help="Run a guarded update, or recover an unfinished transaction."
    )
    run.add_argument(
        "--retry-rolled-back",
        action="store_true",
        help="Explicitly retry a reviewed rolled-back revision.",
    )
    commands.add_parser("status", help="Read the most recent result without changing state.")
    commands.add_parser("rollback", help="Guardedly restore the most recent completed update.")
    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            print(
                setup(
                    args.source.absolute(), args.home.absolute(), args.validation_python.absolute()
                )
            )
            return 0
        settings = load_settings(args.config)
        result = (
            Updater(settings).run(
                rollback=args.command == "rollback",
                retry_rolled_back=getattr(args, "retry_rolled_back", False),
            )
            if args.command in {"run", "rollback"}
            else read_json(settings.state / "latest.json")
        )
        print(json.dumps(result, indent=2))
        return (
            0
            if args.command == "status"
            or result["result"]
            in {
                "current",
                "updated",
                "recovered",
                "rollback-complete",
                "busy",
                "blocked-local-changes",
            }
            else 1
        )
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Toolkit update stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
