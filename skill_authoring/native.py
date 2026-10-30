"""Bounded Codex execution in fresh homes with verified tool filesystem boundaries."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def execute(
    command: list[str], cwd: Path, environment: dict[str, str], text: str = "", seconds: int = 30
) -> dict[str, Any]:
    """Run an argument vector with bounded wall time, output, and process-group cleanup.

    Parameters
    ----------
    command : list[str]
        Program and arguments; no shell interpolation.
    cwd : Path
        Working directory.
    environment : dict[str, str]
        Explicit child environment.
    text : str
        Standard input.
    seconds : int
        Wall deadline in seconds.
    """
    started = time.monotonic()
    expired = False
    with (
        tempfile.TemporaryFile() as source,
        tempfile.TemporaryFile() as out,
        tempfile.TemporaryFile() as err,
    ):
        source.write(text.encode())
        source.seek(0)
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=source,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        try:
            process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            expired = True
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        out.seek(0)
        err.seek(0)
        stdout, stderr = out.read(8_000_001), err.read(8_000_001)
    return {
        "returncode": process.returncode,
        "timed_out": expired,
        "output_limited": len(stdout) > 8_000_000 or len(stderr) > 8_000_000,
        "stdout": stdout[:8_000_000].decode(errors="replace"),
        "stderr": stderr[:8_000_000].decode(errors="replace"),
        "total_duration_seconds": time.monotonic() - started,
    }


def configure(root: Path, codex: Path, model: str, effort: str) -> dict[str, str]:
    """Create a fresh Codex home and a deny-by-default native permission profile."""
    home, client, temporary, workspace = [root / p for p in ("home", "client", "tmp", "workspace")]
    for path in (home, client, temporary, workspace):
        path.mkdir(exist_ok=True)
    environment = {
        "HOME": str(home),
        "CODEX_HOME": str(client),
        "TMPDIR": str(temporary),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": str(workspace.parent),
    }
    subprocess.run(
        ["git", "init", "--quiet", str(workspace)],
        cwd=workspace,
        env=environment,
        check=True,
        capture_output=True,
        timeout=10,
    )
    permissions = {
        ":root": "deny",
        ":minimal": "read",
        ":tmpdir": "deny",
        ":slash_tmp": "deny",
        str(workspace): "write",
        str(temporary): "write",
        str(home): "read",
        str(Path(sys.base_prefix).resolve()): "read",
        str(Path(sys.executable).resolve()): "read",
        str(codex): "read",
    }
    filesystem = ", ".join(f"{json.dumps(k)} = {json.dumps(v)}" for k, v in permissions.items())
    configuration = (
        f"model = {json.dumps(model)}\nmodel_reasoning_effort = {json.dumps(effort)}\n"
        'approval_policy = "never"\ndefault_permissions = "skill_eval"\n'
        'web_search = "disabled"\nallow_login_shell = false\nproject_doc_max_bytes = 0\n'
        "[skills.bundled]\nenabled = false\n[agents]\nenabled = false\n"
        "[features]\napps = false\nplugins = false\nmemories = false\n"
        '[shell_environment_policy]\ninherit = "none"\n[shell_environment_policy.set]\n'
        + "\n".join(f"{k} = {json.dumps(v)}" for k, v in environment.items())
        + f"\n[permissions.skill_eval]\nfilesystem = {{ {filesystem} }}\n"
        + "[permissions.skill_eval.network]\nenabled = false\n"
    )
    (client / "config.toml").write_text(configuration)
    return environment


def preflight(root: Path, codex: Path, environment: dict[str, str]) -> dict[str, Any]:
    """Require positive workspace access and denied controller/alias/network access."""
    outside = root / "controller-canary"
    outside.write_text("private")
    alias = root / "workspace" / "outside-alias"
    alias.symlink_to(outside)
    program = f"""import errno,json,pathlib,socket
root=pathlib.Path({str(root)!r})
checks={{}}
p=root/'workspace'/'allowed';p.write_text('ok');checks['workspace']=p.read_text()=='ok'
targets=[('controller',root/'controller-canary'),('alias',root/'workspace'/'outside-alias'),
         ('config',root/'client'/'config.toml')]
for name,path in targets:
    try:path.read_bytes()
    except PermissionError:checks[name]=True
    except OSError:checks[name]=False
    else:checks[name]=False
try:(root/'outside-write').write_text('bad')
except PermissionError:checks['write']=True
else:checks['write']=False
sock=socket.socket()
try:sock.connect(('127.0.0.1',9))
except OSError as e:checks['network']=e.errno in (errno.EPERM,errno.EACCES)
else:checks['network']=False
finally:sock.close()
print(json.dumps(checks))
"""
    try:
        result = execute(
            [
                str(codex),
                "sandbox",
                "-P",
                "skill_eval",
                "-C",
                str(root / "workspace"),
                str(Path(sys.executable).resolve()),
                "-I",
                "-c",
                program,
            ],
            root / "workspace",
            environment,
        )
        if result["returncode"] != 0 or result["timed_out"]:
            raise ValueError(
                "Codex native sandbox preflight unavailable: " + result["stderr"][-1500:]
            )
        checks: dict[str, Any] = json.loads(result["stdout"])
        expected = {"workspace", "controller", "alias", "config", "write", "network"}
        if (
            not isinstance(checks, dict)
            or set(checks) != expected
            or any(value is not True for value in checks.values())
        ):
            raise ValueError(f"Codex native sandbox checks failed: {checks}")
        return checks
    finally:
        alias.unlink(missing_ok=True)
        (root / "workspace" / "allowed").unlink(missing_ok=True)


def tokens(trace: str) -> int | None:
    """Sum observed root-turn input/output usage; child agents are disabled."""
    total, observed = 0, False
    for line in trace.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage", {})
        values = [usage.get("input_tokens"), usage.get("output_tokens")]
        if any(type(value) is not int or value < 0 for value in values):
            return None
        total += sum(values)
        observed = True
    return total if observed else None
