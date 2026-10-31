#!/usr/bin/env python3
"""Link selected toolkit skills into a local agent host, with reversible backups."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tomllib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
IGNORED = {"__pycache__", ".DS_Store", ".ruff_cache", ".mypy_cache", "node_modules"}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
AGENTS = {
    "codex": {
        "documentation-skill": ["documentation-agent.toml"],
        "ddia-skill": ["ddia-agent.toml"],
        "ddia-assess-skill": ["ddia-agent.toml"],
        "ddia-design-skill": ["ddia-agent.toml"],
        "ddia-review-skill": ["ddia-agent.toml"],
        "ddia-validate-skill": ["ddia-agent.toml"],
        "ddia-migrate-skill": ["ddia-agent.toml"],
        "ddia-operate-skill": ["ddia-agent.toml"],
        "ddia-explain-skill": ["ddia-agent.toml"],
        "software-design-skill": ["software-design-agent.toml"],
        "independent-diff-review-skill": ["adversarial-reviewer-agent.toml", "verifier-agent.toml"],
        "issue-to-tested-pr-skill": [
            "adversarial-reviewer-agent.toml",
            "implementation-owner-agent.toml",
            "verifier-agent.toml",
        ],
    },
    "copilot": {},
}
SKILL_ALIASES = {
    "doc-agent": "documentation-skill",
    "ddia-specialist": "ddia-skill",
    "software-design-specialist": "software-design-skill",
    "independent-diff-review": "independent-diff-review-skill",
    "issue-to-tested-pr": "issue-to-tested-pr-skill",
    "release-and-docs": "release-and-docs-skill",
    "simplify-or-delete": "simplify-or-delete-skill",
}
AGENT_ALIASES = {
    "codex": {
        "doc-agent.toml": "documentation-agent.toml",
        "ddia-specialist.toml": "ddia-agent.toml",
        "software-design-specialist.toml": "software-design-agent.toml",
        "adversarial-reviewer.toml": "adversarial-reviewer-agent.toml",
        "implementation-owner.toml": "implementation-owner-agent.toml",
        "verifier.toml": "verifier-agent.toml",
    },
    "copilot": {},
}
SCHEMA = "agent-toolkit-install/v1"


class InstallError(ValueError):
    """An installation or restoration failed without discarding user content."""


@dataclass(frozen=True)
class Entry:
    """One destination to link, or a legacy destination to move into backup.

    Parameters
    ----------
    area : str
        Key identifying the installation directory.
    name : str
        Single skill or agent filename within that directory.
    source : Path or None
        Canonical source; None means retire a duplicate legacy installation.
    """

    area: str
    name: str
    source: Path | None


def present(path: Path) -> bool:
    """Return whether an entry exists, including a dangling symlink."""
    return os.path.lexists(path)


def validate_tree(path: Path) -> None:
    """Read a complete source tree, rejecting symlinks and special files.

    Parameters
    ----------
    path : Path
        Source directory or regular file. Generated caches are skipped.
    """
    mode = path.lstat().st_mode
    if stat.S_ISDIR(mode):
        with os.scandir(path) as entries:
            children = sorted(entries, key=lambda entry: entry.name)
        for child in children:
            if child.name not in IGNORED:
                validate_tree(Path(child.path))
    elif stat.S_ISREG(mode):
        path.read_bytes()
    else:
        raise InstallError(f"Source must contain only regular files and directories: {path}")


def skill_metadata(path: Path) -> tuple[str, str]:
    """Read the name and description from a skill's simple frontmatter."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if match is None:
        raise InstallError(f"Missing skill frontmatter: {path}")
    fields = {}
    for line in match[1].splitlines():
        key, separator, value = line.partition(":")
        if separator and key in {"name", "description"}:
            fields[key] = value.strip().strip("\"'")
    if not fields.get("name") or not fields.get("description"):
        raise InstallError(f"Skill needs a name and description: {path}")
    return fields["name"], fields["description"]


def inventory(root: Path = ROOT) -> dict[str, str]:
    """Validate the shipped package and return its skill descriptions."""
    for directory in (root / "skills", root / "agents"):
        validate_tree(directory)
    found = {}
    for path in sorted((root / "skills").iterdir()):
        if path.name in IGNORED:
            continue
        if (
            not path.is_dir()
            or NAME.fullmatch(path.name) is None
            or not path.name.endswith("-skill")
        ):
            raise InstallError(f"Invalid skill directory: {path}")
        name, description = skill_metadata(path / "SKILL.md")
        if name != path.name:
            raise InstallError(f"Skill name must match its directory: {path}")
        found[name] = description
    if not found:
        raise InstallError("No skills found in this checkout.")
    for path in (root / "agents").iterdir():
        if path.name not in IGNORED and (not path.is_dir() or path.name not in AGENTS):
            raise InstallError(f"Unknown agent host directory: {path}")
    for target, groups in AGENTS.items():
        expected = {name for names in groups.values() for name in names}
        actual = set()
        directory = root / "agents" / target
        if target == "copilot":
            if any(path.name not in IGNORED for path in directory.glob("*")):
                raise InstallError(
                    "Only Codex agent definitions are shipped; Copilot installs skills only."
                )
            continue
        extension = ".toml"
        for path in sorted(directory.glob("*")):
            if path.name in IGNORED:
                continue
            slug = path.name.removesuffix(extension)
            if (
                not path.is_file()
                or not path.name.endswith(extension)
                or NAME.fullmatch(slug) is None
                or not slug.endswith("-agent")
            ):
                raise InstallError(f"Agent filename must end with -agent{extension}: {path}")
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            for field in ("name", "description", "developer_instructions"):
                if not isinstance(data.get(field), str) or not data[field].strip():
                    raise InstallError(f"Agent {path} needs {field}.")
            if data["name"] != slug.replace("-", "_"):
                raise InstallError(f"Codex agent name must match its filename: {path}")
            actual.add(path.name)
        if actual != expected:
            raise InstallError(
                f"Agent files and mappings differ for {target}: "
                f"missing {sorted(expected - actual)}, unmapped {sorted(actual - expected)}"
            )
        for skill in groups:
            if skill not in found:
                raise InstallError(f"Agent mapping names a missing skill: {skill}")
    return found


def print_catalog(root: Path, skills: dict[str, str]) -> None:
    """List validated skills with the named roles installed for each host.

    Parameters
    ----------
    root : Path
        Toolkit source containing the role metadata validated by ``inventory``.
    skills : dict of str to str
        Skill names and descriptions returned by ``inventory``.
    """
    print("Package catalog: named roles installed when each skill is selected.\n")
    for skill, description in skills.items():
        print(f"{skill}: {description}")
        for host, groups in AGENTS.items():
            names = []
            for filename in groups.get(skill, []):
                path = root / "agents" / host / filename
                name = tomllib.loads(path.read_text(encoding="utf-8"))["name"]
                names.append(name)
            print(f"  {host.title()} roles: {', '.join(names) or 'none (skill only)'}")
        print()


def print_json_catalog(root: Path, skills: dict[str, str]) -> None:
    """Print one versioned catalog object from validated package metadata."""
    previous_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        from project_bootstrap import SKILL_DEPENDENCIES, resolve_skills
    finally:
        sys.dont_write_bytecode = previous_bytecode

    resolve_skills(list(skills), skills)
    entries = []
    for skill in sorted(skills):
        roles = {}
        for host, groups in AGENTS.items():
            roles[host] = sorted(
                tomllib.loads((root / "agents" / host / filename).read_text(encoding="utf-8"))[
                    "name"
                ]
                for filename in groups.get(skill, [])
            )
        entries.append(
            {
                "name": skill,
                "description": skills[skill],
                "dependencies": sorted(SKILL_DEPENDENCIES.get(skill, ())),
                "roles": roles,
            }
        )
    print(json.dumps({"schema_version": 1, "skills": entries}))


def locations(home: Path, codex_home: Path) -> dict[str, Path]:
    """Return host directories without reading or changing host configuration."""
    return {
        "codex-skills": home / ".agents/skills",
        "codex-agents": codex_home / "agents",
        "legacy-codex-skills": codex_home / "skills",
        "copilot-skills": home / ".copilot/skills",
        "copilot-agents": home / ".copilot/agents",
    }


def check_parents(path: Path) -> None:
    """Reject symlinked or non-directory destination ancestors before writes."""
    for parent in (path, *path.parents):
        if present(parent) and (parent.is_symlink() or not parent.is_dir()):
            raise InstallError(f"Expected a real directory, not a link or file: {parent}")


def validate_layout(root: Path, paths: dict[str, Path], storage: Path) -> None:
    """Reject aliases and nesting among source, destination, and backup roots.

    Parameters
    ----------
    root : Path
        Canonical toolkit checkout, which must not contain installation state.
    paths : dict of str to Path
        Active and legacy host directories relevant to this operation.
    storage : Path
        Installation receipt and backup directory.
    """
    directories = {"source checkout": root, **paths, "receipt storage": storage}
    resolved = [(name, path.resolve()) for name, path in directories.items()]
    for index, (name, path) in enumerate(resolved):
        for other_name, other in resolved[index + 1 :]:
            if path.is_relative_to(other) or other.is_relative_to(path):
                raise InstallError(
                    f"Installation locations overlap: {name} ({path}) and "
                    f"{other_name} ({other}). Choose separate source, host, and backup directories."
                )


def linked_to(path: Path, source: Path) -> bool:
    """Recognize exact symbolic links and regular-file hard links to the source."""
    if path.is_symlink():
        return os.readlink(path) == str(source)
    return path.is_file() and source.is_file() and path.samefile(source)


def selected_skills(skills: list[str], available: dict[str, str]) -> list[str]:
    """Resolve personal-install selectors, aliases and shared dependencies."""
    for alias in sorted(set(skills) & SKILL_ALIASES.keys()):
        print(
            f"Deprecated skill selector {alias!r}; use {SKILL_ALIASES[alias]!r}.",
            file=sys.stderr,
        )
    skills = sorted({SKILL_ALIASES.get(name, name) for name in skills})
    unknown = sorted(set(skills) - available.keys())
    if unknown:
        raise InstallError(f"Unknown skills: {', '.join(unknown)}")
    from project_bootstrap import BootstrapError, resolve_skills

    try:
        return resolve_skills(skills, available)
    except BootstrapError as error:
        raise InstallError(str(error)) from error


def installation_status(
    root: Path, target: str, skills: list[str], home: Path, codex_home: Path
) -> list[dict[str, str]]:
    """Inspect expected current links without writing source or host state.

    Linkage establishes neither historical ownership nor permission to replace an
    entry. Legacy and unrelated destinations are outside this selection.
    """
    available = inventory(root)
    previous_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        skills = selected_skills(skills, available)
    finally:
        sys.dont_write_bytecode = previous_bytecode
    paths = locations(home, codex_home)
    expected = {(f"{target}-skills", name): root / "skills" / name for name in skills}
    expected.update(
        {
            (f"{target}-agents", agent): root / "agents" / target / agent
            for name in skills
            for agent in AGENTS[target].get(name, [])
        }
    )
    entries = []
    for (area, name), source in sorted(expected.items()):
        destination = paths[area] / name
        check_parents(destination.parent)
        try:
            mode = destination.lstat().st_mode
        except FileNotFoundError:
            state = "missing"
        else:
            current = False
            if area == "codex-agents":
                current = stat.S_ISREG(mode) and destination.samefile(source)
            elif stat.S_ISLNK(mode):
                current = os.readlink(destination) == str(source)
            state = "current" if current else "different"
        entries.append({"area": area, "name": name, "state": state})
    return entries


def plan_install(
    root: Path, target: str, skills: list[str], paths: dict[str, Path], *, backup_existing: bool
) -> list[Entry]:
    """Preflight selected links and legacy migrations without filesystem writes."""
    skills = selected_skills(skills, inventory(root))
    candidates = []
    for name in skills:
        candidates.append(Entry(f"{target}-skills", name, root / "skills" / name))
        for agent in AGENTS[target].get(name, []):
            candidates.append(Entry(f"{target}-agents", agent, root / "agents" / target / agent))
            for old, canonical in AGENT_ALIASES[target].items():
                if canonical == agent and present(paths[f"{target}-agents"] / old):
                    candidates.append(Entry(f"{target}-agents", old, None))
        for old, canonical in SKILL_ALIASES.items():
            if canonical != name:
                continue
            if present(paths[f"{target}-skills"] / old):
                candidates.append(Entry(f"{target}-skills", old, None))
            if target == "codex" and present(paths["legacy-codex-skills"] / old):
                candidates.append(Entry("legacy-codex-skills", old, None))
        if target == "codex" and present(paths["legacy-codex-skills"] / name):
            candidates.append(Entry("legacy-codex-skills", name, None))
    changes = []
    conflicts = []
    seen: set[tuple[str, str]] = set()
    for entry in candidates:
        key = (entry.area, entry.name)
        if key in seen:
            continue
        seen.add(key)
        destination = paths[entry.area] / entry.name
        check_parents(destination.parent)
        if (
            entry.source is not None
            and linked_to(destination, entry.source)
            and (entry.area != "codex-agents" or not destination.is_symlink())
        ):
            continue
        if present(destination) and not backup_existing:
            conflicts.append(str(destination))
        changes.append(entry)
    if conflicts:
        raise InstallError(
            "Existing entries would change; inspect them and use --backup-existing to preserve "
            "them before replacement:\n" + "\n".join(conflicts)
        )
    return changes


def make_directories(path: Path, created: list[Path]) -> None:
    """Create missing directories and record them for rollback."""
    if path.exists():
        return
    make_directories(path.parent, created)
    path.mkdir()
    created.append(path)


def write_receipt(path: Path, data: dict[str, Any]) -> None:
    """Atomically persist installation state in its private backup directory."""
    temporary = path.with_suffix(".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def install(
    root: Path,
    target: str,
    skills: list[str],
    home: Path,
    codex_home: Path,
    *,
    backup_existing: bool = False,
    dry_run: bool = False,
) -> Path | None:
    """Install a preflighted selection and return its restoration receipt.

    Parameters
    ----------
    root : Path
        Absolute canonical toolkit checkout.
    target : str
        Host name: codex or copilot.
    skills : list of str
        Selected skill directory names.
    home, codex_home : Path
        Explicit destination roots, independent of the current process home.
    backup_existing : bool
        Move conflicting entries into backup before replacing them.
    dry_run : bool
        Print the complete plan without creating any filesystem entries.

    Returns
    -------
    Path or None
        Receipt path, or None when dry-running or already installed.
    """
    paths = locations(home, codex_home)
    areas = [f"{target}-skills", f"{target}-agents"]
    if target == "codex":
        areas.append("legacy-codex-skills")
    storage = home / ".local/state/agent-toolkit/installations"
    validate_layout(root, {area: paths[area] for area in areas}, storage)
    check_parents(storage)
    entries = plan_install(root, target, skills, paths, backup_existing=backup_existing)
    for entry in entries:
        destination = paths[entry.area] / entry.name
        kind = "hard link" if entry.area == "codex-agents" else "symbolic link"
        action = f"{kind} -> {entry.source}" if entry.source else "retire legacy duplicate"
        backup_note = " (back up existing entry)" if present(destination) else ""
        print(f"{destination}: {action}{backup_note}")
    if dry_run or not entries:
        print("Dry run; no changes." if dry_run else "Already installed; no changes.")
        return None
    run = storage / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12])
    receipt = run / "receipt.json"
    data: dict[str, Any] = {
        "schema": SCHEMA,
        "state": "pending",
        "home": str(home),
        "codex_home": str(codex_home),
        "source": str(root),
        "entries": [
            {
                "area": entry.area,
                "name": entry.name,
                "source": str(entry.source) if entry.source else None,
                "backup": present(paths[entry.area] / entry.name),
            }
            for entry in entries
        ],
    }
    created: list[Path] = []
    moved: list[tuple[Path, Path]] = []
    linked: list[tuple[Path, Path]] = []
    try:
        make_directories(run, created)
        run.chmod(0o700)
        write_receipt(receipt, data)
        for index, entry in enumerate(entries):
            destination = paths[entry.area] / entry.name
            make_directories(destination.parent, created)
            if present(destination) != data["entries"][index]["backup"]:
                raise OSError(f"Destination changed during installation: {destination}")
            if present(destination):
                backup = run / str(index)
                destination.rename(backup)
                moved.append((backup, destination))
            if entry.source is not None:
                if entry.area == "codex-agents":
                    # Codex discovers symlinked roles but its runtime uses O_NOFOLLOW.
                    # A hard link is a regular file while retaining the canonical source inode.
                    os.link(entry.source, destination)
                else:
                    destination.symlink_to(entry.source, target_is_directory=entry.source.is_dir())
                linked.append((destination, entry.source))
        data["state"] = "installed"
        write_receipt(receipt, data)
    except OSError as error:
        try:
            for destination, source in reversed(linked):
                if not linked_to(destination, source):
                    raise InstallError(f"Concurrent edit prevents rollback: {destination}")
                destination.unlink()
            for backup, destination in reversed(moved):
                if present(destination):
                    raise InstallError(f"Concurrent edit prevents rollback: {destination}")
                backup.rename(destination)
            if receipt.exists():
                receipt.unlink()
            for directory in reversed(created):
                directory.rmdir()
        except (OSError, InstallError) as rollback_error:
            raise InstallError(
                f"Install failed: {error}. Rollback needs attention: {rollback_error}. "
                f"Preserved backups: {run}"
            ) from error
        raise InstallError(f"Install failed and was rolled back: {error}") from error
    print(f"Installed. Restore receipt: {receipt}")
    return receipt


def check_restore_dependents(
    source_root: Path,
    paths: dict[str, Path],
    operations: list[tuple[Path, Path | None, Path | None]],
) -> None:
    """Refuse to remove resources still needed by surviving installed skills.

    Parameters
    ----------
    source_root : Path
        Canonical source recorded by this receipt; only its managed links are consumers.
    paths : dict of str to Path
        Current host directories derived from the restoration receipt.
    operations : list of tuple
        Fully validated destinations, current sources and optional backups. No source
        tree or other receipt is read, so dangling-link cleanup remains possible.
    """
    from project_bootstrap import SKILL_DEPENDENCIES

    # A backup restores the prior entry rather than deleting the capability. Preserve
    # existing role refresh/symlink migration rollback semantics; this guard prevents
    # removal, not compatibility claims about the restored historical version.
    changing = {
        destination
        for destination, source, backup in operations
        if source is not None and backup is None
    }
    restored = {destination for destination, _, _ in operations}
    for host, associations in AGENTS.items():
        skill_directory, role_directory = paths[f"{host}-skills"], paths[f"{host}-agents"]
        if not any(path.parent in (skill_directory, role_directory) for path in changing):
            continue
        for skill in sorted(set(SKILL_DEPENDENCIES) | set(associations)):
            dependent = skill_directory / skill
            if dependent in restored or not linked_to(dependent, source_root / "skills" / skill):
                continue
            dependencies: set[str] = set()
            pending = list(SKILL_DEPENDENCIES.get(skill, ()))
            while pending:
                dependency = pending.pop()
                if dependency in dependencies:
                    continue
                dependencies.add(dependency)
                pending.extend(SKILL_DEPENDENCIES.get(dependency, ()))
            required = {skill_directory / name for name in dependencies}
            required.update(role_directory / name for name in associations.get(skill, ()))
            affected = required & changing
            if affected:
                names = ", ".join(path.name for path in sorted(affected))
                raise InstallError(
                    f"Restore would remove shared dependencies ({names}) still used by "
                    f"{dependent}. Restore dependent installations first."
                )


def restore(receipt: Path, *, dry_run: bool = False) -> None:
    """Restore a completed installation if all managed destinations still match.

    Parameters
    ----------
    receipt : Path
        Receipt printed by a successful installation.
    dry_run : bool
        Validate restoration without changing files.
    """
    check_parents(receipt.parent)
    if receipt.is_symlink() or not receipt.is_file():
        raise InstallError("Restore requires a regular receipt file.")
    data = json.loads(receipt.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise InstallError("Unsupported restoration receipt.")
    if data.get("state") != "installed":
        raise InstallError("Receipt is not a completed, unrestored installation.")
    home = Path(data["home"])
    codex_home = Path(data["codex_home"])
    storage = home / ".local/state/agent-toolkit/installations"
    if not home.is_absolute() or not codex_home.is_absolute() or receipt.parent.parent != storage:
        raise InstallError("Receipt must remain inside its original installation directory.")
    paths = locations(home, codex_home)
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise InstallError("Receipt contains no installation entries.")
    operations = []
    destinations: set[Path] = set()
    areas: set[str] = set()
    for index, item in enumerate(raw_entries):
        if not isinstance(item, dict):
            raise InstallError("Invalid receipt entry.")
        area, name = item.get("area"), item.get("name")
        if area not in paths or not isinstance(name, str) or not re.fullmatch(r"[\w.-]+", name):
            raise InstallError("Invalid destination in receipt.")
        if name in {".", ".."}:
            raise InstallError("Invalid destination in receipt.")
        destination = paths[area] / name
        if destination in destinations:
            raise InstallError("Duplicate destination in receipt.")
        destinations.add(destination)
        areas.add(area)
        check_parents(destination.parent)
        value = item.get("source")
        if value is not None and (not isinstance(value, str) or not Path(value).is_absolute()):
            raise InstallError("Invalid source in receipt.")
        source = Path(value) if value is not None else None
        if source is None:
            if present(destination):
                raise InstallError(
                    f"Legacy destination has changed; preserve it first: {destination}"
                )
        elif not linked_to(destination, source):
            raise InstallError(
                f"Installed destination has changed; preserve it first: {destination}"
            )
        if not isinstance(item.get("backup"), bool):
            raise InstallError("Invalid backup marker in receipt.")
        backup = receipt.parent / str(index) if item["backup"] else None
        if backup is not None and not present(backup):
            raise InstallError(f"Required backup is missing: {backup}")
        operations.append((destination, source, backup))
    validate_layout(Path(data["source"]), {area: paths[area] for area in areas}, storage)
    check_restore_dependents(Path(data["source"]), paths, operations)
    for destination, _, backup in operations:
        print(f"{destination}: {'restore backup' if backup else 'remove toolkit link'}")
    if dry_run:
        print("Dry run; no changes.")
        return
    removed: list[tuple[Path, Path, bool]] = []
    restored: list[tuple[Path, Path]] = []
    try:
        for destination, source, backup in reversed(operations):
            if source is not None:
                was_symlink = destination.is_symlink()
                destination.unlink()
                removed.append((destination, source, was_symlink))
            if backup is not None:
                backup.rename(destination)
                restored.append((destination, backup))
        data["state"] = "restored"
        write_receipt(receipt, data)
    except OSError as error:
        try:
            for destination, backup in reversed(restored):
                destination.rename(backup)
            for destination, source, was_symlink in reversed(removed):
                if was_symlink:
                    destination.symlink_to(source)
                else:
                    os.link(source, destination)
        except OSError as rollback_error:
            raise InstallError(
                f"Restore failed: {error}; rollback needs attention: {rollback_error}. "
                f"Receipt and remaining backups: {receipt}"
            ) from error
        raise InstallError(f"Restore failed and was rolled back: {error}") from error
    print("Restored. The receipt remains as a record; empty host directories are retained.")


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface and return a process exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser(
        "list", help="List packaged skills and associated named agent roles."
    )
    catalog.add_argument("--json", action="store_true", help="Emit a versioned JSON catalog.")
    commands.add_parser("check", help="Validate package sources without installing.")
    apply = commands.add_parser("install", help="Link selected skills into an agent host.")
    apply.add_argument("--target", choices=tuple(AGENTS), required=True)
    selection = apply.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--skill", action="append", dest="skills", help="Repeat to select skills."
    )
    selection.add_argument("--all", action="store_true")
    apply.add_argument(
        "--home", type=Path, help="Use an isolated home; ignores inherited CODEX_HOME."
    )
    apply.add_argument("--codex-home", type=Path, help="Explicit custom Codex directory.")
    apply.add_argument("--backup-existing", action="store_true")
    apply.add_argument("--dry-run", action="store_true")
    status = commands.add_parser("status", help="Inspect selected personal links without changes.")
    status.add_argument("--target", choices=tuple(AGENTS), required=True)
    status_selection = status.add_mutually_exclusive_group(required=True)
    status_selection.add_argument("--skill", action="append", dest="skills")
    status_selection.add_argument("--all", action="store_true")
    status.add_argument("--home", type=Path, required=True, help="Ignores inherited CODEX_HOME.")
    status.add_argument("--codex-home", type=Path, help="Explicit custom Codex directory.")
    status.add_argument("--json", action="store_true", help="Print one versioned JSON object.")
    undo = commands.add_parser("restore", help="Restore the entries recorded by an installation.")
    undo.add_argument("receipt", type=Path)
    undo.add_argument("--dry-run", action="store_true")
    project = commands.add_parser(
        "bootstrap", help="Copy shared project-local skills and agents into an application."
    )
    project.add_argument("--project", type=Path, required=True)
    project.add_argument("--target", choices=(*AGENTS, "both"))
    project_selection = project.add_mutually_exclusive_group()
    project_selection.add_argument("--skill", action="append", dest="skills")
    project_selection.add_argument("--all", action="store_true")
    project.add_argument("--update", action="store_true")
    project.add_argument("--dry-run", action="store_true")
    project.add_argument(
        "--check", action="store_true", help="Verify recorded project integrity without changes."
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        arguments = sys.argv[1:] if argv is None else argv
        if error.code and arguments and arguments[0] == "status" and "--json" in arguments:
            print(
                json.dumps(
                    {"schema_version": 1, "entries": [], "error": "Invalid status arguments."}
                )
            )
            return 2
        raise
    if args.command == "bootstrap" and args.check:
        incompatible = [
            flag
            for flag, value in (
                ("--update", args.update),
                ("--dry-run", args.dry_run),
                ("--skill", args.skills),
                ("--all", args.all),
                ("--target", args.target),
            )
            if value
        ]
        if incompatible:
            parser.error("--check cannot be combined with " + ", ".join(incompatible))
    try:
        if args.command == "bootstrap" and args.check:
            previous_bytecode = sys.dont_write_bytecode
            try:
                sys.dont_write_bytecode = True
                from project_bootstrap import check_integrity

                check_integrity(args.project)
            finally:
                sys.dont_write_bytecode = previous_bytecode
        elif args.command == "restore":
            restore(args.receipt.expanduser().absolute(), dry_run=args.dry_run)
        else:
            skills = inventory(ROOT)
            if args.command == "list":
                if args.json:
                    print_json_catalog(ROOT, skills)
                else:
                    print_catalog(ROOT, skills)
            elif args.command == "check":
                counts = {
                    host: len({name for names in groups.values() for name in names})
                    for host, groups in AGENTS.items()
                }
                print(
                    f"Package valid: {len(skills)} skills, {counts['codex']} Codex agents, "
                    f"{counts['copilot']} Copilot agents."
                )
            elif args.command == "bootstrap":
                previous_bytecode = sys.dont_write_bytecode
                try:
                    sys.dont_write_bytecode = previous_bytecode or args.dry_run
                    from project_bootstrap import bootstrap
                finally:
                    sys.dont_write_bytecode = previous_bytecode

                selected = list(skills) if args.all else args.skills
                if selected is not None:
                    for alias in sorted(set(selected) & SKILL_ALIASES.keys()):
                        print(
                            f"Deprecated skill selector {alias!r}; use {SKILL_ALIASES[alias]!r}.",
                            file=sys.stderr,
                        )
                    selected = [SKILL_ALIASES.get(name, name) for name in selected]
                bootstrap(
                    ROOT,
                    args.project,
                    skills,
                    AGENTS,
                    IGNORED,
                    skills=selected,
                    target=args.target,
                    update=args.update,
                    dry_run=args.dry_run,
                )
            else:
                try:
                    home = (args.home or Path.home()).expanduser().resolve()
                    inherited = os.environ.get("CODEX_HOME") if args.home is None else None
                    codex_home = (
                        (args.codex_home or (Path(inherited) if inherited else home / ".codex"))
                        .expanduser()
                        .resolve()
                    )
                except RuntimeError as error:
                    if args.command != "status":
                        raise
                    raise InstallError(str(error)) from error
                if args.command == "status":
                    entries = installation_status(
                        ROOT,
                        args.target,
                        list(skills) if args.all else args.skills,
                        home,
                        codex_home,
                    )
                    if args.json:
                        print(json.dumps({"schema_version": 1, "entries": entries}))
                    else:
                        paths = locations(home, codex_home)
                        for entry in entries:
                            print(f"{paths[entry['area']] / entry['name']}: {entry['state']}")
                    return 0 if all(entry["state"] == "current" for entry in entries) else 1
                else:
                    install(
                        ROOT,
                        args.target,
                        list(skills) if args.all else args.skills,
                        home,
                        codex_home,
                        backup_existing=args.backup_existing,
                        dry_run=args.dry_run,
                    )
    except (OSError, ValueError, KeyError, TypeError) as error:
        if args.command == "status" and args.json:
            print(json.dumps({"schema_version": 1, "entries": [], "error": str(error)}))
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
