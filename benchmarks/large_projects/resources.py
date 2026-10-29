"""Kernel-enforced Linux execution cells, owned by one benchmark attempt.

Docker is used only through the explicitly selected local daemon. Candidate cells never
receive its socket, host homes, curator trees, or mutable reference caches. All writable
storage is bounded tmpfs and belongs to the same memory cgroup as every descendant.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks.process import Execution, bounded_process

IMAGE = "busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec"
LABEL = "org.agent-toolkit.attempt"
SELECTORS = ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
CONTROLLER_RESERVE = 2 * 1024**3


@dataclass(frozen=True)
class Limits:
    """Limits apply to an entire cell, including threads, children and tmpfs pages."""

    memory_bytes: int = 8 * 1024**3
    filesystem_bytes: int = 8 * 1024**3
    pids: int = 512
    seconds: float = 3600

    def validate(self) -> None:
        """Reject ineffective or unsupported limits before allocating a cell."""
        if (
            self.memory_bytes < 32 * 1024**2
            or self.filesystem_bytes < 8 * 1024**2
            or self.filesystem_bytes > self.memory_bytes
            or not 8 <= self.pids <= 4096
            or not 0 < self.seconds <= 14400
        ):
            raise ValueError("invalid aggregate memory/filesystem/pid/deadline limits")


class Deadline:
    """One monotonic budget shared by preparation, staging, execution and grading."""

    def __init__(self, seconds: float) -> None:
        self.started = time.monotonic()
        self.expires = self.started + seconds

    def remaining(self, maximum: float | None = None) -> float:
        """Never restart a phase's wall allowance."""
        remaining = self.expires - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("staging-inclusive attempt deadline exhausted")
        return min(remaining, maximum) if maximum is not None else remaining


def docker(
    argv: Sequence[str],
    *,
    timeout: float = 30,
    stdin: str = "",
    max_output: int = 8_000_000,
    stdout_path: Path | None = None,
) -> Execution:
    """Use this environment's managed daemon, preserving registry/proxy configuration."""
    binary = shutil.which("docker")
    if binary is None:
        raise ValueError("Docker is required for enforced aggregate resource limits")
    env = {key: value for key, value in os.environ.items() if key not in SELECTORS}
    return bounded_process(
        [binary, "--host=unix:///var/run/docker.sock", *argv],
        Path("/tmp"),
        env,
        timeout=timeout,
        stdin=stdin,
        max_output=max_output,
        stdout_path=stdout_path,
        enforce_output_files=True,
    )


def require(result: Execution) -> Execution:
    """A daemon/configuration failure is never a candidate failure or passing control."""
    if result.returncode or result.timed_out or result.output_limited:
        raise RuntimeError(f"resource runtime failed: {result.stderr[-3000:]}")
    return result


def system_mounts() -> list[tuple[Path, Path]]:
    """Mount system runtimes without obscuring BusyBox's /lib64 -> /lib link."""
    pairs = [
        (Path("/usr"), Path("/usr")),
        (Path("/usr/bin"), Path("/bin")),
        (Path("/usr/sbin"), Path("/sbin")),
        (Path("/usr/lib/x86_64-linux-gnu"), Path("/lib/x86_64-linux-gnu")),
        (Path("/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"), Path("/lib/ld-linux-x86-64.so.2")),
        (Path(sys.base_prefix).resolve(), Path(sys.base_prefix).resolve()),
    ]
    for name in ("/etc/ld.so.cache", "/etc/alternatives", "/etc/ssl/certs"):
        if Path(name).exists():
            pairs.append((Path(name), Path(name)))
    return pairs


def checked_toolchains(paths: Sequence[Path], private: Sequence[Path]) -> list[Path]:
    """Reject grants that expose curator/controller data, including through aliases."""
    protected = [path.resolve() for path in private]
    for source, _ in system_mounts():
        if any(path.is_relative_to(source.resolve()) for path in protected):
            raise ValueError("private benchmark data is inside an exposed system runtime")
    selected = []
    for path in paths:
        path = path.resolve(strict=True)
        if path in {Path("/"), Path.home()} or not (path / "bin").is_dir():
            raise ValueError("toolchain must be a narrow runtime root with bin/")
        if any(path.is_relative_to(p) or p.is_relative_to(path) for p in protected):
            raise ValueError("toolchain grant overlaps curator, dependency or controller data")
        selected.append(path)
    return selected


class ResourceCell:
    """A persistent quota-backed namespace; removal kills every task-owned descendant."""

    def __init__(
        self,
        root: Path,
        limits: Limits,
        *,
        readonly: Sequence[Path] = (),
        image: str = IMAGE,
        owner: str | None = None,
        deadline: Deadline | None = None,
        system: bool = True,
        client_transport: bool = False,
        native_sandbox: bool = False,
    ) -> None:
        limits.validate()
        if native_sandbox and limits.filesystem_bytes < limits.memory_bytes:
            raise ValueError("nested-sandbox storage budget must cover the global memory bound")
        self.native_sandbox = native_sandbox
        if not re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", image):
            raise ValueError("resource image must be pinned by full SHA-256 digest")
        self.root = root.absolute()
        if self.root == Path("/") or any(c in str(self.root) for c in ",:\n"):
            raise ValueError("unsafe cell root")
        self.limits, self.image = limits, image
        self.owner = owner or str(uuid.uuid4())
        if not re.fullmatch(r"[a-zA-Z0-9-]{1,80}", self.owner):
            raise ValueError("invalid resource ownership label")
        self.name = "toolkit-" + str(uuid.uuid4())
        self.volume = self.name + "-work"
        self.deadline = deadline or Deadline(limits.seconds)
        self.closed = False
        self.paused = False
        self._runtime = tempfile.TemporaryDirectory(prefix="toolkit-cell-runtime-")
        runtime = Path(self._runtime.name)
        (runtime / "passwd").write_text(
            f"benchmark:x:{os.getuid()}:{os.getgid()}:Benchmark:/tmp:/bin/sh\n"
        )
        (runtime / "group").write_text(f"benchmark:x:{os.getgid()}:\n")
        (runtime / "nsswitch.conf").write_text("passwd: files\ngroup: files\nhosts: files\n")
        mounts = system_mounts() if system else []
        mounts += [
            (runtime / name, Path("/etc") / name) for name in ("passwd", "group", "nsswitch.conf")
        ]
        for path in readonly:
            path = path.resolve(strict=True)
            if path == Path("/") or self.root.is_relative_to(path):
                raise ValueError("read-only grant contains mutable execution root")
            mounts.append((path, path))
        # Every writable data mount is accounted for; /dev is not writable by this UID.
        self.shm_bytes = min(32 * 1024**2, limits.filesystem_bytes // 8)
        self.tmp_bytes = min(1024**3, limits.filesystem_bytes // 4)
        self.work_bytes = limits.filesystem_bytes - self.shm_bytes - self.tmp_bytes
        command = [
            "create",
            "--pull=never",
            "--name",
            self.name,
            "--label",
            f"{LABEL}={self.owner}",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--cgroupns=private",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--network",
            "bridge" if client_transport else "none",
            "--log-driver=none",
            "--memory",
            str(limits.memory_bytes),
            "--memory-swap",
            str(limits.memory_bytes),
            "--pids-limit",
            str(limits.pids),
            "--cpus",
            "2",
            "--shm-size",
            str(self.shm_bytes),
            "--mount",
            f"type=volume,source={self.volume},target={self.root},volume-nocopy",
            "--tmpfs",
            f"/tmp:rw,exec,size={self.tmp_bytes},mode=1777",
        ]
        if native_sandbox:
            profile = Path(__file__).parent / "vendor/native-seccomp.json"
            command += [
                "--security-opt",
                f"seccomp={profile}",
                "--security-opt",
                "systempaths=unconfined",
            ]
        for source, target in mounts:
            if not source.exists():
                raise ValueError(f"required system runtime is missing: {source}")
            command += ["--mount", f"type=bind,src={source},dst={target},readonly"]
        if not client_transport:
            for key in (
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
                "http_proxy",
                "https_proxy",
                "all_proxy",
            ):
                command += ["--env", f"{key}="]
        command += ["--entrypoint", "/bin/sleep", image, "infinity"]
        try:
            require(
                docker(
                    [
                        "volume",
                        "create",
                        "--label",
                        f"{LABEL}={self.owner}",
                        "--driver",
                        "local",
                        "--opt",
                        "type=tmpfs",
                        "--opt",
                        "device=tmpfs",
                        "--opt",
                        f"o=size={self.work_bytes},uid={os.getuid()},gid={os.getgid()},mode=700",
                        self.volume,
                    ],
                    timeout=self.deadline.remaining(30),
                )
            )
            require(docker(command, timeout=self.deadline.remaining(60)))
            require(docker(["start", self.name], timeout=self.deadline.remaining(30)))
            self.enforcement = self.inspect_enforcement()
        except BaseException:
            self.close()
            raise

    def execute(
        self,
        argv: Sequence[str],
        cwd: Path | None = None,
        *,
        stdin: str = "",
        environment: dict[str, str] | None = None,
        timeout: float = 30,
    ) -> Execution:
        """Run inside the existing cell, never increasing its original remaining deadline."""
        if self.closed or self.paused:
            raise ValueError("resource cell is not running")
        command = ["exec", "-i", "--workdir", str(cwd or self.root)]
        for key, value in (environment or {}).items():
            command += ["--env", f"{key}={value}"]
        return docker(
            [*command, self.name, *argv], stdin=stdin, timeout=self.deadline.remaining(timeout)
        )

    def inspect_enforcement(self) -> dict[str, Any]:
        """Check actual kernel limits, not only options accepted by the Docker client."""
        result = require(
            self.execute(
                [
                    "/bin/sh",
                    "-c",
                    "cat /sys/fs/cgroup/memory.max; cat /sys/fs/cgroup/memory.swap.max; "
                    "cat /sys/fs/cgroup/pids.max; cat /sys/fs/cgroup/cpu.max",
                ],
                timeout=10,
            )
        )
        values = result.stdout.splitlines()
        if (
            len(values) != 4
            or values[0] != str(self.limits.memory_bytes)
            or values[1] != "0"
            or values[2] != str(self.limits.pids)
        ):
            raise ValueError("kernel cgroup limits do not match requested resource budget")
        quota, period = values[3].split()
        if quota == "max" or int(quota) / int(period) > 2:
            raise ValueError("kernel CPU quota is missing")
        return {
            "memory_max": int(values[0]),
            "swap_max": 0,
            "pids_max": int(values[2]),
            "cpu_max": values[3],
            "filesystem_bytes": self.limits.filesystem_bytes,
            "tmpfs": {
                str(self.root): self.work_bytes,
                "/tmp": self.tmp_bytes,
                "/dev/shm": self.shm_bytes,
            },
            "image": self.image,
            "storage_accounting": "allocated tmpfs pages; staged data charged inside memory cgroup",
            "nested_mount_guard": "global memory bound"
            if self.native_sandbox
            else "default seccomp",
        }

    def upload(self, source: Path, target: Path) -> None:
        """Copy only explicitly staged input; do not mount an answer-bearing host parent."""
        if not target.is_relative_to(self.root):
            raise ValueError("input destination escapes quota-backed storage")
        # Docker's upload initially charges daemon pages. Re-copy inside the cell
        # before any payload runs, then delete that seed; every remaining writable
        # page is materialized by a process in this cell's memory cgroup.
        staging = self.root / (".upload-" + str(uuid.uuid4()))
        require(self.execute(["/bin/mkdir", "-p", str(staging)], timeout=10))
        try:
            require(
                docker(
                    ["cp", "--archive", str(source), f"{self.name}:{staging}/input"],
                    timeout=self.deadline.remaining(300),
                )
            )
            require(
                self.execute(
                    ["/bin/cp", "-a", "--reflink=never", str(staging / "input"), str(target)],
                    timeout=300,
                )
            )
        finally:
            require(self.execute(["/bin/rm", "-rf", str(staging)], timeout=30))

    def freeze(self) -> None:
        """Suspend all descendants before the controller reads artifact bytes."""
        require(docker(["pause", self.name], timeout=self.deadline.remaining(15)))
        self.paused = True

    def download(self, source: Path, destination: Path) -> None:
        """Capture a frozen raw tar; never let Docker extract candidate paths on the host."""
        if not self.paused or not source.is_relative_to(self.root) or destination.exists():
            raise ValueError("artifact download requires a frozen cell and new destination")
        available = shutil.disk_usage(destination.parent).free - CONTROLLER_RESERVE
        if available < 1024**2:
            raise ValueError("insufficient controller disk for a bounded artifact transfer")
        require(
            docker(
                ["cp", f"{self.name}:{source}", "-"],
                timeout=self.deadline.remaining(300),
                stdout_path=destination,
                max_output=min(self.limits.filesystem_bytes, available),
            )
        )

    def events(self) -> dict[str, int]:
        """Read kernel OOM/resource counters before removing the execution cell."""
        result = require(self.execute(["/bin/cat", "/sys/fs/cgroup/memory.events"], timeout=10))
        return {
            name: int(value)
            for name, value in (line.split() for line in result.stdout.splitlines())
        }

    def close(self) -> None:
        """Cleanup has its own bounded grace, even after the work deadline expires."""
        if self.closed:
            return
        self.closed = True
        result = docker(
            ["inspect", "--format", '{{index .Config.Labels "' + LABEL + '"}}', self.name],
            timeout=10,
        )
        if result.returncode == 0:
            if result.stdout.strip() != self.owner:
                raise ValueError("refusing cleanup of a container owned by another attempt")
            require(docker(["rm", "--force", "--volumes", self.name], timeout=15))
        volume = docker(
            ["volume", "inspect", "--format", '{{index .Labels "' + LABEL + '"}}', self.volume],
            timeout=10,
        )
        if volume.returncode == 0:
            if volume.stdout.strip() != self.owner:
                raise ValueError("refusing cleanup of a volume owned by another attempt")
            require(docker(["volume", "rm", self.volume], timeout=15))
        self._runtime.cleanup()

    def __enter__(self) -> ResourceCell:
        """Return the active execution cell."""
        return self

    def __exit__(self, *_: Any) -> None:
        """Always terminate descendants and release task-owned storage."""
        self.close()


def cleanup_owned(owner: str) -> dict[str, Any]:
    """Remove only resources carrying this invocation's unpredictable ownership label."""
    removed: list[str] = []
    errors: list[str] = []
    for kind, listing, removal in (
        ("container", ["ps", "-aq"], ["rm", "--force", "--volumes"]),
        ("volume", ["volume", "ls", "-q"], ["volume", "rm"]),
    ):
        result = docker([*listing, "--filter", f"label={LABEL}={owner}"], timeout=10)
        if result.returncode:
            errors.append(f"cannot list owned {kind}: {result.stderr[-1000:]}")
            continue
        for identifier in result.stdout.splitlines():
            if not re.fullmatch(r"[a-zA-Z0-9-]+", identifier):
                errors.append("invalid resource identifier")
                continue
            result = docker([*removal, identifier], timeout=15)
            if result.returncode:
                errors.append(f"cannot remove owned {kind}: {result.stderr[-1000:]}")
            else:
                removed.append(f"{kind}:{identifier}")
    return {"complete": not errors, "removed": removed, "errors": errors}
