"""Fail-closed Codex CLI adapter and explicitly staged source/toolkit profiles."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import stat
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Any

import install
from benchmarks.cases import REPOSITORY
from benchmarks.process import Execution, bounded_process, sanitized_environment

HARNESS_ROOT = Path(__file__).resolve().parent

ARMS = ("baseline", "source-matched", "toolkit")
PROFILES = ("downloaded", "reference-complete")
SOURCE_LIBRARIES = {
    "ddia-skill": "ddia-specialist",
    "software-design-skill": "software-design-specialist",
}


def skill_names() -> tuple[str, ...]:
    """Use the installer's validated canonical inventory for all staged skills."""
    return tuple(install.inventory(REPOSITORY))


DISABLED = (
    "apps",
    "plugins",
    "memories",
    "memory_tool",
    "external_agent_memory_import",
    "chronicle",
    "hooks",
    "codex_hooks",
    "plugin_hooks",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "in_app_browser",
    "request_permissions_tool",
    "request_permissions",
    "shell_snapshot",
    "shell_snapshot_v2",
    "image_generation",
    "imagegenext",
    "connectors",
    "remote_control",
    "remote_plugin",
    "recommended_plugins",
    "workspace_dependencies",
    "skill_mcp_dependency_install",
    "skill_env_var_dependency_prompt",
    "daemon_auto_start",
    "search_tool",
    "standalone_web_search",
)


def digest(path: Path) -> str:
    """Fingerprint a regular non-symlink file."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(values: Any) -> str:
    """Fingerprint structured comparison metadata deterministically."""
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def harness_fingerprint() -> str:
    """Bind plans to every Python source file in the executing benchmark package."""
    files = {
        str(path.relative_to(HARNESS_ROOT)): digest(path)
        for path in sorted(HARNESS_ROOT.rglob("*.py"))
        if "__pycache__" not in path.parts
    }
    if not files:
        raise ValueError("benchmark harness sources are missing")
    files["../install.py"] = digest(Path(install.__file__).resolve())
    package = HARNESS_ROOT / "large_projects"
    for path in [*package.glob("*.json"), *package.glob("controls/*"), *package.glob("vendor/*")]:
        if path.is_file():
            files[str(path.relative_to(HARNESS_ROOT))] = digest(path)
    return fingerprint(files)


@cache
def git_runtime() -> tuple[Path, Path, str]:
    """Resolve real Git and its helper directory without using macOS's sandboxed shim."""
    environment = sanitized_environment(Path("/var/empty"), Path("/tmp"))
    executable: Path | None = None
    if platform.system() == "Darwin":
        selected = bounded_process(
            ["/usr/bin/xcrun", "--find", "git"], REPOSITORY, environment, timeout=5
        )
        if selected.returncode == 0 and selected.stdout.strip():
            executable = Path(selected.stdout.strip()).resolve(strict=True)
    if executable is None:
        found = shutil.which("git")
        if found is None:
            raise ValueError("Git is unavailable")
        executable = Path(found).resolve(strict=True)
    version = bounded_process([str(executable), "--version"], REPOSITORY, environment, timeout=5)
    helpers = bounded_process([str(executable), "--exec-path"], REPOSITORY, environment, timeout=5)
    if version.returncode != 0 or helpers.returncode != 0:
        raise ValueError("selected Git runtime does not start")
    helper_path = Path(helpers.stdout.strip()).resolve(strict=True)
    if not helper_path.is_dir() or helper_path in {Path("/"), Path.home()}:
        raise ValueError("Git helper runtime root is invalid")
    return executable, helper_path, version.stdout.strip()


def stage_runtime(actor_home: Path) -> dict[str, str]:
    """Expose canonical Python/Git through the isolated actor PATH without host config."""
    binary_directory = actor_home / "bin"
    binary_directory.mkdir(exist_ok=True)
    git, helpers, version = git_runtime()
    for name, target in (
        ("python", Path(sys.executable).resolve()),
        ("python3", Path(sys.executable).resolve()),
        ("git", git),
    ):
        destination = binary_directory / name
        if destination.is_symlink() and destination.resolve() == target:
            continue
        destination.symlink_to(target)
    return {"executable": str(git), "exec_path": str(helpers), "version": version}


def resource_manifest(profile: str, manifest: Path | None = None) -> dict[str, Path]:
    """Resolve only downloaded content or explicitly supplied, fingerprinted reference files.

    A complete profile requires source and index for both retrieval specialists. It does not
    silently import personal studies or search the user's library. Existing evaluation material
    is excluded from both arms.
    """
    if profile not in PROFILES:
        raise ValueError("unknown resource profile")
    resources: dict[str, Path] = {}
    for path in sorted((REPOSITORY / "books").glob("*.epub")):
        resources[f"books/{path.name}"] = path
    for skill in skill_names():
        directory = REPOSITORY / "skills" / skill
        for kind in ("references", "scripts", "assets"):
            for path in sorted((directory / kind).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    resources[f".agents/skills/{skill}/{path.relative_to(directory)}"] = path
    if profile == "reference-complete":
        if manifest is None:
            raise ValueError("reference-complete requires an explicit source manifest")
        data = json.loads(manifest.read_text())
        if data.get("version") != 1 or not isinstance(data.get("files"), list):
            raise ValueError("source manifest requires version:1 and files array")
        for entry in data["files"]:
            target = Path(entry["target"])
            if (
                target.is_absolute()
                or ".." in target.parts
                or len(target.parts) < 4
                or target.parts[:2] != (".local", "share")
                or target.parts[2] not in set(SOURCE_LIBRARIES.values())
                or any("eval" in part.lower() or "rubric" in part.lower() for part in target.parts)
                or target.name in {"AGENTS.md", "SKILL.md"}
            ):
                raise ValueError(f"unsafe/private-evaluation source target: {target}")
            source = Path(entry["source"]).expanduser()
            if digest(source) != entry["sha256"]:
                raise ValueError(f"source fingerprint mismatch: {target}")
            if str(target) in resources:
                raise ValueError(f"duplicate source target: {target}")
            resources[str(target)] = source
        required = {
            f".local/share/{skill}/{name}"
            for skill in SOURCE_LIBRARIES.values()
            for name in ("source.epub", "index.json")
        }
        if not required <= resources.keys():
            raise ValueError(f"incomplete references: {sorted(required - resources.keys())}")
        for skill in SOURCE_LIBRARIES.values():
            prefix = f".local/share/{skill}"
            index = json.loads(resources[f"{prefix}/index.json"].read_text())
            if index.get("source_sha256") != digest(resources[f"{prefix}/source.epub"]):
                raise ValueError(f"source/index mismatch: {skill}")
    elif manifest is not None:
        raise ValueError("downloaded profile cannot silently include external sources")
    return resources


def toolkit_manifest() -> dict[str, str]:
    """Fingerprint the current toolkit package before every staging boundary."""
    return {
        str(path.relative_to(REPOSITORY)): digest(path)
        for directory in ("agents", "skills")
        for path in sorted((REPOSITORY / directory).rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def stage_arm(
    actor_home: Path,
    client_home: Path,
    arm: str,
    profile: str,
    model: str,
    effort: str,
    mode: str = "controlled",
    source_manifest: Path | None = None,
) -> dict[str, Any]:
    """Copy real toolkit resources/roles into isolated homes without altering installation."""
    if arm not in ARMS or mode not in {"controlled", "shipped"}:
        raise ValueError("invalid arm or model mode")
    resources = resource_manifest(profile, source_manifest)
    git = stage_runtime(actor_home)
    source_hashes = {target: digest(path) for target, path in resources.items()}
    toolkit_hashes: dict[str, str] = {}
    if arm != "baseline":
        for target, source in resources.items():
            destination = actor_home / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            if digest(destination) != source_hashes[target]:
                raise ValueError("source changed during staging")
    if arm == "toolkit":
        for skill in skill_names():
            source = REPOSITORY / "skills" / skill / "SKILL.md"
            skill_target = actor_home / ".agents" / "skills" / skill / "SKILL.md"
            skill_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, skill_target)
            toolkit_hashes[str(source.relative_to(REPOSITORY))] = digest(source)
            if digest(skill_target) != digest(source):
                raise ValueError("skill changed during staging")
        for source in sorted((REPOSITORY / "agents/codex").glob("*.toml")):
            data = tomllib.loads(source.read_text())
            # Parent permissions are authoritative. Legacy role sandbox keys are removed in
            # both modes so they cannot override the verified permission profile.
            data.pop("sandbox_mode", None)
            if mode == "controlled":
                data["model"] = model
                data["model_reasoning_effort"] = effort
            role_target = client_home / "agents" / source.name
            role_target.parent.mkdir(parents=True, exist_ok=True)
            role_target.write_text(
                "\n".join(f"{key} = {json.dumps(value)}" for key, value in data.items()) + "\n"
            )
            toolkit_hashes[str(source.relative_to(REPOSITORY))] = digest(source)
    return {
        "git_runtime": git,
        "source_files": source_hashes,
        "source_fingerprint": fingerprint(source_hashes),
        "toolkit_files": toolkit_hashes,
        "toolkit_fingerprint": fingerprint(toolkit_hashes),
        "resource_profile": profile,
        "model_mode": mode,
        "missing_references": (
            [
                "software-design original source/index",
                "DDIA extracted index and optional personal studies",
            ]
            if profile == "downloaded"
            else []
        ),
        "source_access_observed": [],
        "role_dispatch_observed": [],
    }


def permission_config(workspace: Path, readonly: Sequence[Path], temporary: Path) -> str:
    """Build deny-by-default native filesystem and network permissions."""
    permissions = {
        ":root": "deny",
        ":minimal": "read",
        str(workspace.resolve()): "write",
        str(temporary.resolve()): "write",
    }
    for path in readonly:
        permissions[str(path.resolve())] = "read"
    # Python may be a Homebrew/uv runtime outside minimal system paths. Permit its specific
    # runtime tree, never the Python project, a user's home, or a package-manager cache root.
    runtime = Path(sys.base_prefix).resolve()
    if runtime == Path.home() or runtime == Path("/"):
        raise ValueError("Python runtime root is too broad")
    permissions[str(runtime)] = "read"
    executable = Path(sys.executable).resolve()
    permissions[str(executable)] = "read"
    codex = shutil.which("codex")
    if codex:
        permissions[str(Path(codex).absolute())] = "read"
        permissions[str(Path(codex).resolve())] = "read"
    git, helpers, _ = git_runtime()
    permissions[str(git)] = "read"
    permissions[str(helpers)] = "read"
    body = ", ".join(
        f"{json.dumps(key)} = {json.dumps(value)}" for key, value in permissions.items()
    )
    return (
        f"[permissions.benchmark]\nfilesystem = {{ {body} }}\n"
        "[permissions.benchmark.network]\nenabled = false\n"
    )


def config_text(
    workspace: Path,
    actor_home: Path,
    client_home: Path,
    temporary: Path,
    model: str,
    effort: str,
    budget_units: int | None = None,
    *,
    local_network: bool = False,
    readonly_extra: Sequence[Path] = (),
    shell_environment: dict[str, str] | None = None,
    project_guidance: bool = False,
) -> str:
    """Generate isolated client configuration, including tree-wide bounded rollout units."""
    readonly = [actor_home, *readonly_extra]
    if (client_home / "agents").exists():
        readonly.append(client_home / "agents")
    lines = [
        f"model = {json.dumps(model)}",
        f"model_reasoning_effort = {json.dumps(effort)}",
        'approval_policy = "never"',
        'default_permissions = "benchmark"',
        'web_search = "disabled"',
        "allow_login_shell = false",
        f"project_doc_max_bytes = {32768 if project_guidance else 0}",
        "[skills.bundled]",
        "enabled = false",
        "[shell_environment_policy]",
        'inherit = "none"',
        "[shell_environment_policy.set]",
    ]
    environment = sanitized_environment(actor_home, temporary)
    environment["GIT_CEILING_DIRECTORIES"] = str(workspace.resolve().parent)
    environment.update(shell_environment or {})
    lines += [f"{key} = {json.dumps(value)}" for key, value in environment.items()]
    lines += ["[features]"] + [f"{name} = false" for name in DISABLED]
    if local_network:
        lines += [
            "network_proxy = true",
            "code_mode = true",
            "code_mode_only = true",
            "code_mode_host = true",
            "multi_agent = true",
            "multi_agent_v2 = true",
        ]
    if budget_units is not None:
        if budget_units < 2:
            raise ValueError("budget units must be at least two")
        lines += [
            "[features.rollout_budget]",
            "enabled = true",
            f"limit_tokens = {budget_units}",
            "prefill_token_weight = 1.0",
            "sampling_token_weight = 1.0",
            f"reminder_at_remaining_tokens = [{max(1, budget_units // 4)}]",
        ]
    lines += [
        "[agents]",
        "enabled = true",
        "max_concurrent_threads_per_session = 3",
        f"default_subagent_model = {json.dumps(model)}",
        f"default_subagent_reasoning_effort = {json.dumps(effort)}",
    ]
    permissions = permission_config(workspace, readonly, temporary)
    if local_network:
        permissions = permissions.replace(
            "[permissions.benchmark.network]\nenabled = false",
            '[permissions.benchmark.network]\nenabled = true\nmode = "limited"\n'
            "allow_local_binding = true\n[permissions.benchmark.network.domains]\n"
            '"localhost" = "allow"\n"127.0.0.1" = "allow"',
        )
    lines += [permissions]
    return "\n".join(lines) + "\n"


class NativeExecutor:
    """Execute candidate commands with the same verified native deny-by-default profile."""

    def __init__(
        self, codex: Path, client_home: Path, actor_home: Path, temporary: Path, workspace: Path
    ) -> None:
        self.codex = codex
        self.client_home = client_home
        self.actor_home = actor_home
        self.workspace = workspace.resolve()
        self.environment = sanitized_environment(actor_home, temporary)
        self.environment["CODEX_HOME"] = str(client_home)
        self.environment["GIT_CEILING_DIRECTORIES"] = str(self.workspace.parent)
        self.verified = False

    def for_workspace(self, workspace: Path) -> NativeExecutor:
        """Create and verify an independent boundary for a fresh consumer directory."""
        client = workspace.parent / (workspace.name + "-client")
        temporary = workspace.parent / (workspace.name + "-tmp")
        client.mkdir()
        temporary.mkdir()
        (client / "config.toml").write_text(
            config_text(workspace, self.actor_home, client, temporary, "unused", "low")
        )
        result = NativeExecutor(self.codex, client, self.actor_home, temporary, workspace)
        result.preflight([self.client_home / "config.toml", REPOSITORY / "README.md"])
        return result

    def execute(
        self, argv: Sequence[str], cwd: Path, *, stdin: str = "", timeout: float = 30
    ) -> Execution:
        """Refuse candidate execution before isolation canaries succeed."""
        if not self.verified:
            raise ValueError("native isolation has not passed preflight")
        if not cwd.resolve().is_relative_to(self.workspace):
            raise ValueError("candidate working directory escapes its workspace")
        return self._execute(argv, cwd, stdin=stdin, timeout=timeout)

    def _execute(
        self, argv: Sequence[str], cwd: Path, *, stdin: str = "", timeout: float = 30
    ) -> Execution:
        command = [str(self.codex), "sandbox", "-P", "benchmark", "-C", str(cwd), *argv]
        return bounded_process(command, cwd, self.environment, stdin=stdin, timeout=timeout)

    def preflight(self, forbidden: Sequence[Path]) -> list[dict[str, Any]]:
        """Require positive workspace access plus read/write/alias/network denial evidence."""
        if platform.system() not in {"Darwin", "Linux"}:
            raise ValueError("unsupported native sandbox platform")
        if not forbidden:
            raise ValueError("native preflight requires known existing forbidden files")
        host_targets = []
        for path in forbidden:
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("forbidden preflight target must be a real regular file")
            host_targets.append(
                {
                    "path": str(path.resolve()),
                    "device": metadata.st_dev,
                    "inode": metadata.st_ino,
                    "size": metadata.st_size,
                }
            )
        with tempfile.NamedTemporaryFile(
            dir=self.actor_home, prefix=".isolation-readonly-", delete=False
        ) as stream:
            stream.write(b"known-readonly")
            readonly_control = Path(stream.name)
        control = self.workspace / ".isolation-control"
        control.write_text("allowed")
        alias = self.workspace / ".isolation-alias"
        alias.symlink_to(forbidden[0])
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        paths = [str(path.resolve()) for path in forbidden] + [str(alias)]
        source = f"""import json, pathlib, socket, subprocess
out={{}}
root=pathlib.Path({str(self.workspace)!r})
out['allowed_read']=(root/'.isolation-control').read_text()=='allowed'
(root/'.isolation-write').write_text('allowed')
out['allowed_write']=(root/'.isolation-write').read_text()=='allowed'
out['allowed_readonly_read']=pathlib.Path({str(readonly_control)!r}).read_text()=='known-readonly'
version=subprocess.run(['git','--version'],capture_output=True,text=True,timeout=5)
out['allowed_git_version']=version.returncode==0 and version.stdout.startswith('git version ')
(root/'.isolation-different').write_text('different')
diff=subprocess.run(['git','--no-pager','diff','--no-index','--no-ext-diff','--no-textconv',
                     '--','.isolation-control','.isolation-different'],
                    capture_output=True,text=True,timeout=5)
out['allowed_git_diff']=(diff.returncode==1 and '-allowed' in diff.stdout
                         and '+different' in diff.stdout)
configuration=subprocess.run(['git','config','--global','--list'],
                             capture_output=True,text=True,timeout=5)
out['isolated_git_config']=configuration.returncode==0 and not configuration.stdout.strip()
for index,name in enumerate({paths!r}):
    try:
        pathlib.Path(name).read_bytes()
    except OSError as error:
        out['denied_read_'+str(index)]=error.errno in (1,2,13)
    else:
        out['denied_read_'+str(index)]=False
try:
    pathlib.Path({str(readonly_control)!r}).write_text('bad')
except OSError as error:
    out['denied_write']=error.errno in (1,13,30)
else:
    out['denied_write']=False
try:
    (root/'.isolation-hardlink').hardlink_to({str(forbidden[0].resolve())!r})
except OSError as error:
    out['denied_hardlink']=error.errno in (1,2,13)
else:
    out['denied_hardlink']=False
try:
    socket.create_connection(('127.0.0.1',{port}),timeout=1).close()
except PermissionError:
    out['denied_network']=True
except OSError as error:
    out['denied_network']=error.errno in (1,13)
else:
    out['denied_network']=False
print(json.dumps(out))
"""
        try:
            result = self._execute(
                [str(Path(sys.executable).resolve()), "-I", "-B", "-c", source], self.workspace
            )
            if result.returncode != 0:
                raise ValueError(f"native sandbox preflight failed: {result.stderr[-2000:]}")
            evidence = json.loads(result.stdout)
            expected = 9 + len(paths)
            if len(evidence) != expected or not all(value is True for value in evidence.values()):
                raise ValueError(f"isolation canaries failed: {evidence}")
            for path, expected_target in zip(forbidden, host_targets, strict=True):
                metadata = path.lstat()
                if (metadata.st_dev, metadata.st_ino, metadata.st_size) != (
                    expected_target["device"],
                    expected_target["inode"],
                    expected_target["size"],
                ):
                    raise ValueError("host-positive preflight target changed during the probe")
            if readonly_control.read_text() != "known-readonly":
                raise ValueError("native command overwrote protected source data")
            self.verified = True
            return [
                {
                    "checks": evidence,
                    "host_positive_targets": host_targets,
                    "denial_modes": "permission denied or mount-hidden known existing target",
                    "execution": result.to_dict(),
                }
            ]
        finally:
            listener.close()
            readonly_control.unlink(missing_ok=True)
            for path in (
                control,
                alias,
                self.workspace / ".isolation-write",
                self.workspace / ".isolation-different",
                self.workspace / ".isolation-hardlink",
            ):
                path.unlink(missing_ok=True)


def resolve_codex(path: str = "codex") -> Path:
    """Require a real supported CLI binary, preserving its launcher path."""
    found = shutil.which(path)
    if found is None:
        raise ValueError("Codex CLI unavailable; isolation cannot be established")
    return Path(found).resolve()


def session_projection(path: Path) -> dict[str, Any]:
    """Read bounded rollout metadata, excluding identities, instructions and inherited turns."""
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        try:
            information = os.fstat(file_descriptor)
            if not stat.S_ISREG(information.st_mode) or information.st_nlink != 1:
                raise ValueError("nonregular session metadata")
            stream = os.fdopen(file_descriptor, "rb")
        except BaseException:
            os.close(file_descriptor)
            raise
        with stream:
            line = stream.readline(1_000_001)
            if len(line) > 1_000_000:
                raise ValueError("session header exceeds limit")
            event = json.loads(line)
            if event.get("type") != "session_meta" or not isinstance(event.get("payload"), dict):
                raise ValueError("session header missing")
            payload = event["payload"]
            source = payload.get("source")
            subagent = source.get("subagent") if isinstance(source, dict) else None
            spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
            result = {
                "thread_id": payload.get("id"),
                "parent_thread_id": None,
                "agent_role": None,
                "model": None,
                "effort": None,
            }
            if not isinstance(spawn, dict):
                return result
            result["parent_thread_id"] = spawn.get("parent_thread_id")
            result["agent_role"] = spawn.get("agent_role")
            if not isinstance(result["parent_thread_id"], str) or (
                result["agent_role"] is not None and not isinstance(result["agent_role"], str)
            ):
                raise ValueError("invalid child thread metadata")
            if payload.get("agent_role") not in {None, result["agent_role"]}:
                raise ValueError("conflicting session role metadata")
            # Codex defines this as the first ordinal in the child's own projected history.
            # Earlier turn_context records may describe the parent's different model/effort.
            start = payload.get("subagent_history_start_ordinal")
            if type(start) is not int or start < 1:
                return result
            total = len(line)
            for ordinal in range(1, 4096):
                line = stream.readline(1_000_001)
                if not line:
                    break
                total += len(line)
                if len(line) > 1_000_000 or total > 16_000_000:
                    break
                if ordinal < start:
                    continue
                event = json.loads(line)
                if event.get("type") == "turn_context" and isinstance(event.get("payload"), dict):
                    for key in ("model", "effort"):
                        value = event["payload"].get(key)
                        if isinstance(value, str):
                            result[key] = value
                    break
            return result
    finally:
        os.close(descriptor)


def observe_run_sessions(client_home: Path | None, root_thread_id: str | None) -> dict[str, Any]:
    """Observe only descendants of stdout's root in this invocation's isolated session tree."""
    result: dict[str, Any] = {
        "root_thread_id": root_thread_id,
        "observations": [],
        "status": "unavailable",
        "headers_inspected": 0,
        "warnings": [],
        "scope": "this run's client-home/sessions only; no global session search",
    }
    if client_home is None or root_thread_id is None:
        return result
    if client_home.is_symlink() or (client_home / "sessions").is_symlink():
        result["warnings"].append("session directory alias rejected")
        return result
    sessions = client_home.resolve() / "sessions"
    if not sessions.is_dir():
        return result
    records: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    for index, path in enumerate(sorted(sessions.rglob("*.jsonl"))):
        if index >= 256:
            result["warnings"].append("session file inspection limit reached")
            break
        try:
            record = session_projection(path)
            result["headers_inspected"] += 1
            identifier = record["thread_id"]
            if not isinstance(identifier, str):
                raise ValueError("session thread identity missing")
            record["evidence"] = "local session_meta.source.subagent.thread_spawn"
            record["session_file"] = str(path.relative_to(sessions))
            if identifier in records:
                conflicts.add(identifier)
                result["warnings"].append("duplicate session thread identity")
            records[identifier] = record
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            result["warnings"].append("unreadable or unsupported session metadata")
    known = {root_thread_id}
    observations = []
    while True:
        added = []
        for identifier, record in records.items():
            if (
                identifier not in known
                and identifier not in conflicts
                and record["parent_thread_id"] in known
                and (record["agent_role"] is None or bool(record["agent_role"]))
            ):
                added.append(record)
        if not added:
            break
        observations.extend(added)
        known.update(record["thread_id"] for record in added)
    result["observations"] = observations
    result["status"] = (
        "partial"
        if result["warnings"]
        else "observed"
        if root_thread_id in records or observations
        else "unavailable"
    )
    return result


def observe_trace(text: str, client_home: Path | None = None) -> dict[str, Any]:
    """Extract actual events and parent-bound local session metadata, never catalog claims."""
    events: list[dict[str, Any]] = []
    usage: dict[str, Any] | None = None
    dispatch: list[dict[str, Any]] = []
    source_calls: list[dict[str, Any]] = []
    root_thread_id: str | None = None
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        if event.get("type") == "thread.started" and root_thread_id is None:
            identifier = event.get("thread_id")
            if isinstance(identifier, str):
                root_thread_id = identifier
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        item = event.get("item", {})
        if isinstance(item, dict):
            item_type = item.get("type", "")
            if item_type == "collab_tool_call" and item.get("tool") == "spawn_agent":
                dispatch.append(item)
            command = item.get("command", "")
            if (
                item_type == "command_execution"
                and isinstance(command, str)
                and item.get("status") == "completed"
                and item.get("exit_code") == 0
                and re.search(
                    r"(?:book\.py\s+(?:read|search|catalog)|source\.epub|/references/)", command
                )
            ):
                source_calls.append(
                    {"command": command, "evidence": "successful command, not proof of reading"}
                )
    session_evidence = observe_run_sessions(client_home, root_thread_id)
    observations = list(session_evidence["observations"])
    known = {record["thread_id"] for record in observations}
    for event in dispatch:
        receivers = event.get("receiver_thread_ids")
        if (
            not isinstance(receivers, list)
            or not receivers
            or not all(isinstance(receiver, str) for receiver in receivers)
            or not set(receivers) <= known
        ):
            observations.append({"evidence": "stdout spawn event", "event": event})
    return {
        "event_count": len(events),
        "reported_root_usage": usage,
        "aggregate_tree_tokens": None,
        "cost": None,
        "role_dispatch_observed": observations,
        "stdout_role_dispatch_events": dispatch,
        "session_dispatch_evidence": session_evidence,
        "source_access_observed": source_calls,
        "accounting_note": "Root turn usage is not assumed to include children; unknown is null.",
    }
