"""Bounded subprocess execution; untrusted submissions additionally require native isolation."""

from __future__ import annotations

import os
import resource
import signal
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class Execution:
    """Observable result of one external process."""

    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool = False
    output_limited: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible execution record."""
        return asdict(self)


class Executor(Protocol):
    """Command boundary used by objective oracles."""

    def for_workspace(self, workspace: Path) -> Executor:
        """Create a boundary for a fresh controller-owned workspace."""
        ...

    def execute(
        self, argv: Sequence[str], cwd: Path, *, stdin: str = "", timeout: float = 30
    ) -> Execution:
        """Execute under this boundary's restrictions."""
        ...


def sanitized_environment(home: Path, temporary: Path) -> dict[str, str]:
    """Build a small environment without inherited credentials or Python injection."""
    return {
        "PATH": f"{home}/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
        "HOME": str(home),
        "TMPDIR": str(temporary),
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ATTR_NOSYSTEM": "1",
    }


def bounded_process(
    argv: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    *,
    stdin: str = "",
    timeout: float = 30,
    max_output: int = 8_000_000,
    stdout_path: Path | None = None,
    enforce_output_files: bool = False,
) -> Execution:
    """Run with a shared wall deadline, bounded captured output, and process-group cleanup.

    Parameters
    ----------
    argv
        Exact argument vector; no shell interpretation.
    cwd
        Explicit working directory.
    environment
        Explicit child environment, never inherited implicitly.
    stdin
        Input text, staged before process startup to avoid pipe deadlock.
    timeout
        Maximum wall seconds for this process group.
    max_output
        Maximum bytes retained in either output stream.
    """
    if timeout <= 0:
        return Execution(list(argv), -signal.SIGKILL, "", "deadline exhausted", 0, True)
    started = time.monotonic()
    timed_out = False
    output_limited = False

    def bound_capture_files() -> None:
        # Only opted-in controller clients (Docker) use this; candidate build files
        # have their own cell quotas. A fast producer cannot fill a host output file
        # between polling intervals.
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_output, max_output))

    with (
        tempfile.TemporaryFile() as input_file,
        stdout_path.open("x+b") if stdout_path else tempfile.TemporaryFile() as output_file,
        tempfile.TemporaryFile() as error_file,
    ):
        input_file.write(stdin.encode())
        input_file.seek(0)
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=dict(environment),
            stdin=input_file,
            stdout=output_file,
            stderr=error_file,
            start_new_session=True,
            preexec_fn=bound_capture_files if enforce_output_files else None,
        )
        try:
            while process.poll() is None:
                timed_out = time.monotonic() - started >= timeout
                output_limited = (
                    os.fstat(output_file.fileno()).st_size > max_output
                    or os.fstat(error_file.fileno()).st_size > max_output
                )
                if timed_out or output_limited:
                    break
                time.sleep(0.02)
        finally:
            # Also terminate background children left behind by a completed parent.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        output_limited = output_limited or (
            os.fstat(output_file.fileno()).st_size > max_output
            or os.fstat(error_file.fileno()).st_size > max_output
        )
        output_file.seek(0)
        error_file.seek(0)
        return Execution(
            list(argv),
            process.returncode,
            "" if stdout_path else output_file.read(max_output).decode(errors="replace"),
            error_file.read(max_output).decode(errors="replace"),
            time.monotonic() - started,
            timed_out,
            output_limited,
        )


class TrustedControlExecutor:
    """Run only repository-owned reference/mutant controls; never user submissions.

    This is deliberately not an isolation claim. It allows credential-free deterministic CI.
    """

    def for_workspace(self, workspace: Path) -> Executor:
        """Retain trusted-control execution for a separately staged consumer."""
        return self

    def execute(
        self, argv: Sequence[str], cwd: Path, *, stdin: str = "", timeout: float = 30
    ) -> Execution:
        """Execute a trusted development control in a fresh process."""
        return bounded_process(
            argv, cwd, sanitized_environment(cwd, cwd), stdin=stdin, timeout=timeout
        )
