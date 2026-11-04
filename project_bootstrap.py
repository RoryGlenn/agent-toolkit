"""Copy a portable, owned agent toolkit layer into an application repository."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "agent-toolkit-project/v1"
MANIFEST = ".agent-toolkit/manifest.json"
BLOCK_START = b"<!-- AGENT_TOOLKIT:START -->"
BLOCK_END = b"<!-- AGENT_TOOLKIT:END -->"
DEFAULT_SKILLS = (
    "documentation-skill",
    "ddia-skill",
    "software-design-skill",
    "independent-diff-review-skill",
    "issue-to-tested-pr-skill",
    "release-and-docs-skill",
    "simplify-or-delete-skill",
)
DDIA_WORKFLOWS = ("assess", "design", "review", "validate", "migrate", "operate", "explain")
ROUTING_SKILL = "task-routing-skill"
SKILL_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    skill: (ROUTING_SKILL,) for skill in DEFAULT_SKILLS
}
SKILL_DEPENDENCIES.update(
    {f"ddia-{mode}-skill": ("ddia-skill", ROUTING_SKILL) for mode in DDIA_WORKFLOWS}
)
HOST_DIRECTORIES = {"codex": ".codex/agents", "copilot": ".github/agents"}
INHERITED_SETTINGS = {"model", "model_reasoning_effort", "sandbox_mode"}
ROUTES = {
    ROUTING_SKILL: "Outside-domain, mixed-domain and changed-topic task routing",
    "documentation-skill": "Documentation, explanations, and reader task success",
    "ddia-skill": "Consequential data architecture, transactions, retries, and recovery",
    "software-design-skill": "Consequential module boundaries, APIs, and maintenance complexity",
    "independent-diff-review-skill": "Independent review of a pull request, branch, or patch",
    "issue-to-tested-pr-skill": "Accepted nontrivial implementation, fixes, and refactoring",
    "release-and-docs-skill": "Release, package, and documentation verification",
    "simplify-or-delete-skill": "Evidence-backed reduction of unnecessary complexity",
}
ROUTES.update(
    {
        f"ddia-{mode}-skill": purpose
        for mode, purpose in zip(
            DDIA_WORKFLOWS,
            (
                "Assess whether a proposed data mechanism is necessary",
                "Design data architecture from workload and invariants",
                "Review consequential data-system changes and generated rules",
                "Validate data invariants under concurrency and failures",
                "Migrate schemas, data, and derived state compatibly",
                "Operate data systems, overload response, and recovery",
                "Explain DDIA concepts through the current project",
            ),
            strict=True,
        )
    }
)


def resolve_skills(skills: list[str], available: dict[str, str]) -> list[str]:
    """Include shared resources required by selected, independently callable skills.

    Parameters
    ----------
    skills : list of str
        Canonical names requested by the caller.
    available : dict of str to str
        Validated package inventory.

    Returns
    -------
    list of str
        Sorted dependency closure; unknown and missing dependencies are rejected.
    """
    selected = set(skills)
    pending = list(selected)
    while pending:
        name = pending.pop()
        if name not in available:
            raise BootstrapError(f"Unknown or missing required skill: {name}")
        for dependency in SKILL_DEPENDENCIES.get(name, ()):
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return sorted(selected)


class BootstrapError(ValueError):
    """A project bootstrap cannot safely proceed with its current inputs."""


@dataclass(frozen=True)
class FileState:
    """Content and permissions of a regular file, retained for ordinary-error rollback."""

    content: bytes
    mode: int = 0o644


def digest(content: bytes) -> str:
    """Return the SHA-256 content identifier used by the ownership manifest."""
    return hashlib.sha256(content).hexdigest()


def check_ancestors(path: Path) -> None:
    """Reject symlinked or non-directory ancestors without resolving them away."""
    for parent in (path, *path.parents):
        if os.path.lexists(parent) and (
            parent.is_symlink() or not stat.S_ISDIR(parent.lstat().st_mode)
        ):
            raise BootstrapError(f"Expected a real directory, not a link or file: {parent}")


def read_file(path: Path) -> FileState | None:
    """Read a regular destination while refusing links and special files."""
    check_ancestors(path.parent)
    if not os.path.lexists(path):
        return None
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise BootstrapError(f"Expected a regular file, not a link or special file: {path}")
    return FileState(path.read_bytes(), stat.S_IMODE(mode))


def render_codex(source: bytes) -> bytes:
    """Remove personal settings only when TOML proves no other semantics changed."""
    text = source.decode("utf-8")
    original = tomllib.loads(text)
    expected = {key: value for key, value in original.items() if key not in INHERITED_SETTINGS}
    rendered = re.sub(
        r"^(?:model|model_reasoning_effort|sandbox_mode)[ \t]*=[^\r\n]*(?:\r?\n|$)",
        "",
        text,
        flags=re.MULTILINE,
    )
    try:
        actual = tomllib.loads(rendered)
    except tomllib.TOMLDecodeError as error:
        raise BootstrapError("Cannot safely render portable Codex role settings.") from error
    if actual != expected:
        raise BootstrapError("Cannot safely render portable Codex role settings.")
    return rendered.encode("utf-8")


def instruction_block(skills: list[str]) -> bytes:
    """Render selected task routes without importing toolkit contributor instructions."""
    lines = [
        BLOCK_START.decode(),
        "## Shared engineering guidance",
        "",
        "Use this project's existing architecture, stack, package manager, commands, and",
        "terminology. Existing project guidance remains authoritative within system and user",
        "instructions. Resolve project facts from the repository before applying reusable advice.",
        "",
        "Load the relevant installed skill when its task applies:",
        "",
    ]
    for skill in skills:
        purpose = ROUTES.get(skill, "Use when the skill's stated task applies")
        lines.append(f"- {purpose}: [{skill}](.agents/skills/{skill}/SKILL.md).")
    if ROUTING_SKILL in skills:
        lines.extend(
            [
                "",
                "At each user turn, route by the current requested outcome, not the selected",
                "agent's default persona. For outside-domain, mixed-domain or changed-topic work,",
                "read .agents/skills/task-routing-skill/SKILL.md. Use only installed capabilities:",
                "simple questions can load the relevant skill directly; consequential bounded",
                "analysis can consult an available specialist. Keep one owner, preserve explicit",
                "no-delegation and edit constraints, and report unavailable capabilities honestly.",
                "An assigned subtask returns to its owner rather than recursively rerouting.",
                "Trivial requests need no routing workflow. "
                "Delegation does not change the UI picker.",
            ]
        )
    if "ddia-skill" in skills:
        lines.extend(
            [
                "",
                "During project design or consequential changes to data ownership, schemas,",
                "transactions, replication, messaging, processing, or recovery, use ddia-skill",
                "to identify applicable invariants and the simplest sufficient design.",
                "Its references/workflows provide assess, design, review, validate, migrate,",
                "operate, and explain procedures; load only the relevant procedure and topics.",
                "Record agreed data contracts and decision evidence in existing project docs,",
                "using its assets only when useful. Changes to prose or UI alone need no DDIA",
                "review. Advice is not a mandatory gate; executable checks enforce explicitly",
                "agreed requirements. The project owner retains implementation authority.",
            ]
        )
    lines.extend(
        [
            "",
            "For nontrivial engineering changes, assign one source-code writer and use relevant",
            "independent review and verification when delegation is available. Routine tasks do",
            "not need a panel of agents. Follow selected skills' fallback instructions when a host",
            "cannot dispatch a named role; disclose unavailable independent evidence.",
            "",
            "Run the project's actual applicable checks and report exact commands and results.",
            "Preserve unrelated work and the user's authorization. Source books and private",
            "studies are optional local resources; disclose missing evidence without claiming it",
            "was consulted. Resolve scripts relative to the skill file that was actually loaded.",
            "",
            "Name future reusable instruction packages <task-or-domain>-skill, matching their",
            "directory and SKILL.md name; display names end in Skill. Name Codex definitions",
            "<role-or-domain>-agent.toml with matching snake_case ..._agent identifiers.",
            "Named roles use only Codex TOML; other hosts can use portable skills directly.",
            "Specialist describes expertise, not an artifact type. Keep host-required SKILL.md",
            "and skill UI metadata agents/openai.yaml filenames unchanged.",
            BLOCK_END.decode(),
        ]
    )
    return "\n".join(lines).encode("utf-8")


def block_span(content: bytes) -> tuple[int, int] | None:
    """Find one complete, standalone managed block or reject ambiguous markers."""
    counts = (content.count(BLOCK_START), content.count(BLOCK_END))
    if counts == (0, 0):
        return None
    if counts != (1, 1):
        raise BootstrapError("AGENTS.md has incomplete or duplicate toolkit block markers.")
    start = content.index(BLOCK_START)
    end = content.index(BLOCK_END) + len(BLOCK_END)
    if (
        end <= start
        or (start and content[start - 1 : start] != b"\n")
        or content[end : end + 1] not in (b"", b"\n", b"\r")
    ):
        raise BootstrapError("AGENTS.md toolkit block markers must be ordered standalone lines.")
    return start, end


def source_identity(root: Path, files: dict[str, FileState], block: bytes) -> dict[str, Any]:
    """Record optional source Git facts and an exact portable-content fingerprint."""
    commit: str | None = None
    dirty: bool | None = None
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        if Path(top).resolve() == root.resolve():
            commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
            dirty = bool(
                subprocess.run(
                    [
                        "git",
                        "--no-optional-locks",
                        "-C",
                        str(root),
                        "status",
                        "--porcelain=v1",
                        "--untracked-files=normal",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=10,
                ).stdout
            )
    except (OSError, subprocess.SubprocessError):
        commit, dirty = None, None
    content = {name: digest(state.content) for name, state in sorted(files.items())}
    content["AGENTS.md:managed-block"] = digest(block)
    fingerprint = digest(json.dumps(content, sort_keys=True).encode())
    return {"commit": commit, "dirty": dirty, "content_sha256": fingerprint}


def validate_manifest(content: bytes, available: dict[str, str] | None = None) -> dict[str, Any]:
    """Validate relative ownership records before trusting any destination path."""

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BootstrapError(f"Duplicate key in project manifest: {key!r}")
            result[key] = value
        return result

    try:
        data = json.loads(content, object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BootstrapError(f"Malformed project toolkit manifest: {error}") from error
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise BootstrapError("Unsupported project toolkit manifest.")
    for key, allowed in (("skills", available), ("hosts", HOST_DIRECTORIES)):
        names = data.get(key)
        if (
            not isinstance(names, list)
            or not names
            or any(
                not isinstance(name, str)
                or (
                    name not in allowed
                    if allowed is not None
                    else re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-skill", name) is None
                )
                for name in names
            )
            or names != sorted(set(names))
        ):
            raise BootstrapError(f"Invalid or unavailable {key} in project manifest.")
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise BootstrapError("Project manifest contains no owned files.")
    for name, fingerprint in files.items():
        if not isinstance(name, str):
            raise BootstrapError("Invalid owned path in project manifest.")
        path = PurePosixPath(name)
        parts = path.parts
        skill_path = (
            len(parts) >= 4 and parts[:2] == (".agents", "skills") and parts[2] in data["skills"]
        )
        # Historical roles can disappear from the current source associations.
        # Their recorded host, canonical filename, and content hash bound ownership.
        role_path = len(parts) == 3 and any(
            parts[:2] == PurePosixPath(HOST_DIRECTORIES[host]).parts
            and re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*-agent"
                + (r"\.toml" if host == "codex" else r"\.agent\.md"),
                parts[2],
            )
            is not None
            for host in data["hosts"]
        )
        if (
            path.is_absolute()
            or path.as_posix() != name
            or ".." in parts
            or "\\" in name
            or not (skill_path or role_path)
        ):
            raise BootstrapError(f"Invalid owned path in project manifest: {name!r}")
        if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
            raise BootstrapError("Invalid owned content hash in project manifest.")
    block_hash = data.get("agents_block_sha256")
    if not isinstance(block_hash, str) or re.fullmatch(r"[0-9a-f]{64}", block_hash) is None:
        raise BootstrapError("Invalid AGENTS.md block hash in project manifest.")
    source = data.get("source")
    if (
        not isinstance(source, dict)
        or "commit" not in source
        or (
            source["commit"] is not None
            and (
                not isinstance(source["commit"], str)
                or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source["commit"]) is None
            )
        )
        or "dirty" not in source
        or (source["dirty"] is not None and not isinstance(source["dirty"], bool))
        or not isinstance(source.get("content_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", source["content_sha256"]) is None
    ):
        raise BootstrapError("Invalid source provenance in project manifest.")
    return data


def check_integrity(project: Path) -> None:
    """Verify recorded project content without loading current sources or planning writes."""
    project = Path(os.path.abspath(project.expanduser()))
    check_ancestors(project)
    manifest = read_file(project / MANIFEST)
    if manifest is None:
        raise BootstrapError(f"Project is not bootstrapped; missing {MANIFEST}: {project}")
    previous = validate_manifest(manifest.content)
    problems = []
    for name, fingerprint in sorted(previous["files"].items()):
        try:
            current = read_file(project / name)
            if current is None:
                problems.append(f"Missing managed file: {name}")
            elif digest(current.content) != fingerprint:
                problems.append(f"Edited managed file: {name}")
        except (OSError, BootstrapError) as error:
            problems.append(f"Unsafe or unreadable managed file {name}: {error}")
    try:
        agents = read_file(project / "AGENTS.md")
        span = block_span(agents.content) if agents else None
        if agents is None or span is None:
            problems.append("Missing managed AGENTS.md routing block.")
        elif digest(agents.content[span[0] : span[1]]) != previous["agents_block_sha256"]:
            problems.append("Edited managed AGENTS.md routing block.")
    except (OSError, BootstrapError) as error:
        problems.append(f"Invalid managed AGENTS.md routing block: {error}")
    if problems:
        raise BootstrapError("Project toolkit integrity check failed:\n" + "\n".join(problems))
    print(
        f"Project toolkit integrity intact: {len(previous['files'])} managed files and AGENTS.md."
    )


def collect_files(
    root: Path,
    skills: list[str],
    hosts: list[str],
    agents: dict[str, dict[str, list[str]]],
    ignored: set[str],
) -> dict[str, FileState]:
    """Snapshot selected skill trees and host roles as regular portable file content."""
    files = {}
    for skill in skills:
        directory = root / "skills" / skill
        for source in sorted(directory.rglob("*")):
            relative = source.relative_to(directory)
            if any(part in ignored for part in relative.parts):
                continue
            if source.is_dir() and not source.is_symlink():
                continue
            state = read_file(source)
            if state is None:
                raise BootstrapError(f"Source disappeared while planning: {source}")
            files[f".agents/skills/{skill}/{relative.as_posix()}"] = state
    for host in hosts:
        names = {name for skill in skills for name in agents[host].get(skill, [])}
        for name in sorted(names):
            source = root / "agents" / host / name
            state = read_file(source)
            if state is None:
                raise BootstrapError(f"Missing source role: {source}")
            if host == "codex":
                state = FileState(render_codex(state.content), state.mode)
            files[f"{HOST_DIRECTORIES[host]}/{name}"] = state
    return files


def write_file(path: Path, state: FileState) -> None:
    """Atomically replace one file without following a preexisting file symlink."""
    descriptor, temporary_name = tempfile.mkstemp(prefix=".agent-toolkit-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(state.content)
        temporary.chmod(state.mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply_changes(
    changes: dict[Path, FileState | None], before: dict[Path, FileState | None]
) -> None:
    """Apply a fully preflighted plan, rolling back ordinary failures in process."""
    created: list[Path] = []
    written: list[Path] = []

    def make_parents(directory: Path) -> None:
        if directory.exists():
            check_ancestors(directory)
            return
        make_parents(directory.parent)
        directory.mkdir()
        created.append(directory)

    try:
        for path, desired in changes.items():
            if read_file(path) != before[path]:
                raise BootstrapError(f"Destination changed during bootstrap: {path}")
            if desired is None:
                path.unlink()
            else:
                make_parents(path.parent)
                write_file(path, desired)
            written.append(path)
    except (OSError, BootstrapError) as error:
        try:
            for path in reversed(written):
                if read_file(path) != changes[path]:
                    raise BootstrapError(f"Concurrent edit prevents rollback: {path}")
                previous = before[path]
                if previous is None:
                    path.unlink()
                else:
                    write_file(path, previous)
            for directory in reversed(created):
                directory.rmdir()
        except (OSError, BootstrapError) as rollback_error:
            raise BootstrapError(
                f"Bootstrap failed: {error}. Rollback needs attention: {rollback_error}. "
                "Inspect the project Git diff before retrying."
            ) from error
        raise BootstrapError(f"Bootstrap failed and was rolled back: {error}") from error


def bootstrap(
    root: Path,
    project: Path,
    available: dict[str, str],
    agents: dict[str, dict[str, list[str]]],
    ignored: set[str],
    *,
    skills: list[str] | None = None,
    target: str | None = None,
    update: bool = False,
    dry_run: bool = False,
) -> None:
    """Copy selected toolkit content into a project with explicit ownership and updates.

    Parameters
    ----------
    root : Path
        Validated toolkit source checkout or unpacked source archive.
    project : Path
        Application directory, which may not yet exist.
    available : dict of str to str
        Skill inventory validated by the CLI before planning.
    agents : dict
        Existing host-to-skill role associations from the personal installer.
    ignored : set of str
        Generated directory and file names excluded from toolkit sources.
    skills, target : optional
        Explicit selection; otherwise reuse a manifest or the engineering defaults.
    update, dry_run : bool
        Permit changes to unchanged owned files, or only print the complete plan.
    """
    project = Path(os.path.abspath(project.expanduser()))
    check_ancestors(project)
    source = root.resolve()
    boundaries = [".agents/skills", *HOST_DIRECTORIES.values(), ".agent-toolkit", "AGENTS.md"]
    for relative in boundaries:
        destination = project / relative
        if destination.is_relative_to(source) or source.is_relative_to(destination):
            raise BootstrapError("Project managed destinations overlap the toolkit source.")
    manifest_path = project / MANIFEST
    existing_manifest = read_file(manifest_path)
    previous = (
        validate_manifest(existing_manifest.content, available)
        if existing_manifest is not None
        else None
    )
    if update and previous is None:
        raise BootstrapError("--update requires an existing project toolkit manifest.")
    selected = resolve_skills(
        list(
            skills if skills is not None else (previous["skills"] if previous else DEFAULT_SKILLS)
        ),
        available,
    )
    hosts = (
        sorted(HOST_DIRECTORIES if target == "both" else [target])
        if target
        else (previous["hosts"] if previous else sorted(HOST_DIRECTORIES))
    )
    if not selected or set(selected) - available.keys():
        raise BootstrapError(f"Unknown or empty skill selection: {selected}")
    if not hosts or any(host not in HOST_DIRECTORIES for host in hosts):
        raise BootstrapError(f"Unknown host selection: {hosts}")
    # Version one stores the full selection, not requested roots. Preserve every old
    # package while permitting only newly required dependencies during explicit update.
    expected_selection = resolve_skills(previous["skills"], available) if previous else selected
    if previous and (selected != expected_selection or hosts != previous["hosts"]):
        raise BootstrapError(
            "Changing project skills or hosts is not supported by this manifest version. "
            "Keep the recorded selection; manage a deliberate reconfiguration through project Git."
        )
    files = collect_files(root, selected, hosts, agents, ignored)
    block = instruction_block(selected)
    agents_path = project / "AGENTS.md"
    current_agents = read_file(agents_path)
    agents_content = current_agents.content if current_agents else b""
    span = block_span(agents_content)
    if previous:
        if (
            span is None
            or digest(agents_content[span[0] : span[1]]) != previous["agents_block_sha256"]
        ):
            raise BootstrapError(
                "Managed AGENTS.md block was edited or removed; preserve it first."
            )
        updated_agents = agents_content[: span[0]] + block + agents_content[span[1] :]
    else:
        if span is not None:
            raise BootstrapError("AGENTS.md has a toolkit block without an ownership manifest.")
        separator = b"\n\n" if agents_content else b""
        updated_agents = agents_content + separator + block + b"\n"
    manifest = {
        "schema": SCHEMA,
        "hosts": hosts,
        "skills": selected,
        "source": source_identity(root, files, block),
        "files": {name: digest(state.content) for name, state in sorted(files.items())},
        "agents_block_sha256": digest(block),
    }
    old_files = previous["files"] if previous else {}
    before: dict[Path, FileState | None] = {}
    changes: dict[Path, FileState | None] = {}
    for name in sorted(set(files) | set(old_files)):
        path = project / name
        current = read_file(path)
        before[path] = current
        if name in old_files:
            if current is None or digest(current.content) != old_files[name]:
                raise BootstrapError(
                    f"Managed file was edited or removed; preserve it first: {path}"
                )
        elif current is not None:
            raise BootstrapError(f"Unmanaged destination already exists: {path}")
        desired = files.get(name)
        if current != desired:
            changes[path] = desired
    before[agents_path] = current_agents
    desired_agents = FileState(updated_agents, current_agents.mode if current_agents else 0o644)
    if desired_agents != current_agents:
        changes[agents_path] = desired_agents
    desired_manifest = FileState((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    before[manifest_path] = existing_manifest
    if desired_manifest != existing_manifest:
        changes[manifest_path] = desired_manifest  # Commit the ownership record last.
    if previous and changes and not update:
        raise BootstrapError(
            "Project toolkit changes are available; inspect --update --dry-run first."
        )
    if not changes:
        print("Already bootstrapped; no changes.")
        return
    for path, state in changes.items():
        action = "remove owned file" if state is None else "update" if before[path] else "create"
        print(f"{path.relative_to(project)}: {action}")
    if dry_run:
        print("Dry run; no changes.")
        return
    apply_changes(changes, before)
    print("Project toolkit ready. Review and commit the generated files with your application.")
