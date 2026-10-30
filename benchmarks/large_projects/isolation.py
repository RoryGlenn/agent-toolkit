"""Linux command isolation for model-free large-project controls.

Only explicitly selected source/dependency paths and system runtimes are mounted.
No host network, home, curator repository, or global configuration is inherited.
"""

from __future__ import annotations

import os
import shutil
import socket
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from benchmarks.process import Execution, bounded_process, sanitized_environment


class LinuxBoundary:
    """A separate PID/network/mount namespace for each task-owned process tree."""

    def __init__(self, writable: Path, readonly: Sequence[Path] = ()) -> None:
        self.writable = writable.resolve(strict=True)
        self.readonly = [path.resolve(strict=True) for path in readonly]
        self.binary = shutil.which("bwrap")
        if not self.binary or os.uname().sysname != "Linux":
            raise ValueError("large-project execution requires Linux and Bubblewrap")
        for path in self.readonly:
            if path == Path("/") or self.writable.is_relative_to(path):
                raise ValueError("read grant contains the writable workspace")
        self._runtime_directory = tempfile.TemporaryDirectory(prefix="benchmark-namespace-")
        self.runtime = Path(self._runtime_directory.name)
        files = {
            "passwd": f"benchmark:x:{os.getuid()}:{os.getgid()}:Benchmark:/tmp:/bin/sh\n",
            "group": f"benchmark:x:{os.getgid()}:\n",
            "hosts": "127.0.0.1 localhost\n::1 localhost\n",
            "nsswitch.conf": "passwd: files\ngroup: files\nhosts: files\n",
        }
        for name, content in files.items():
            (self.runtime / name).write_text(content)

    def close(self) -> None:
        """Remove controller-owned account files after command trees have stopped."""
        self._runtime_directory.cleanup()

    def execute(
        self,
        argv: Sequence[str],
        cwd: Path,
        *,
        environment: dict[str, str] | None = None,
        timeout: float = 30,
    ) -> Execution:
        """Run a command with local-only networking and no outer process visibility."""
        command = [
            self.binary or "bwrap",
            "--unshare-all",
            "--die-with-parent",
            "--new-session",
            "--cap-drop",
            "ALL",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
        ]
        for name in ("/usr", "/bin", "/sbin", "/lib", "/lib64"):
            if Path(name).exists():
                command += ["--ro-bind", name, name]
        for name in ("/etc/ld.so.cache", "/etc/alternatives", "/etc/ssl/certs"):
            if Path(name).exists():
                command += ["--ro-bind", name, name]
        for name in ("passwd", "group", "hosts", "nsswitch.conf"):
            command += ["--ro-bind", str(self.runtime / name), f"/etc/{name}"]
        for path in self.readonly:
            command += ["--ro-bind", str(path), str(path)]
        command += ["--bind", str(self.writable), str(self.writable), "--chdir", str(cwd)]
        env = sanitized_environment(self.writable / "home", self.writable / "tmp")
        env.update({"LC_ALL": "C", "LANG": "C", **(environment or {})})
        # Explicit environment must not be able to import host configuration.
        command += ["--clearenv"]
        for key, value in env.items():
            command += ["--setenv", key, value]
        command += ["--", *argv]
        return bounded_process(command, self.writable, {}, timeout=timeout)

    def preflight(self, forbidden: Sequence[Path]) -> list[dict[str, Any]]:
        """Require positive execution plus filesystem, symlink, Git and network denial."""
        for path in forbidden:
            if not path.is_file():
                raise ValueError(f"missing canary target: {path}")
        with tempfile.TemporaryDirectory(dir=self.writable, prefix="canary-") as directory:
            root = Path(directory)
            for name in ("home", "tmp"):
                (self.writable / name).mkdir(exist_ok=True)
            inside = root / "inside"
            inside.write_text("allowed")
            alias = root / "escape"
            alias.symlink_to(forbidden[0])
            objects = Path(tempfile.mkdtemp(prefix="outside-git-canary-"))
            host_env = sanitized_environment(objects, objects)
            init = bounded_process(
                ["/usr/bin/git", "init", "--bare", "--template=", str(objects)], objects, host_env
            )
            stored = bounded_process(
                ["/usr/bin/git", "--git-dir", str(objects), "hash-object", "-w", "--stdin"],
                objects,
                host_env,
                stdin="outside-object-canary",
            )
            oid = stored.stdout.strip()
            if init.returncode or stored.returncode or len(oid) != 40:
                shutil.rmtree(objects)
                raise ValueError("failed to create positive outside Git object canary")
            gitdir = root / ".git"
            gitdir.write_text(f"gitdir: {objects}\n")
            listener = socket.socket()
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            script = (
                "import pathlib,socket\n"
                f"p=pathlib.Path({str(inside)!r}); assert p.read_text()=='allowed'\n"
                "p.write_text('written')\n"
                f"for name in {[str(p) for p in [*forbidden, alias]]!r}:\n"
                " try: pathlib.Path(name).read_bytes()\n"
                " except OSError: pass\n"
                " else: raise AssertionError('outside read succeeded: '+name)\n"
                "s=socket.socket(); s.settimeout(1)\n"
                f"try: s.connect(('127.0.0.1',{port}))\n"
                "except OSError: pass\n"
                "else: raise AssertionError('host loopback connection succeeded')\n"
                "print('boundary canaries passed')\n"
            )
            try:
                result = self.execute(["/usr/bin/python3", "-c", script], root)
                if result.returncode or result.timed_out:
                    raise ValueError(f"isolation canary failed: {result.to_dict()}")
                git = self.execute(["/usr/bin/git", "cat-file", "-p", oid], root)
                if git.returncode == 0:
                    raise ValueError("outside Git object directory was accessible")
                return [result.to_dict(), git.to_dict()]
            finally:
                listener.close()
                shutil.rmtree(objects)
