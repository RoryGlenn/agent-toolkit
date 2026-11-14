"""Provision a disposable Linux runner and invoke the existing model-free qualification CLI."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[2]
ARCHIVES = {
    "go": (
        "https://dl.google.com/go/go1.26.0.linux-amd64.tar.gz",
        "aac1b08a0fb0c4e0a7c1555beb7b59180b05dfc5a3d62e40e9de90cd42f88235",
    ),
    "node": (
        "https://nodejs.org/dist/v22.22.1/node-v22.22.1-linux-x64.tar.xz",
        "9a6bc82f9b491279147219f6a18add1e18424dce90d41d2a5fcd69d4924ba3aa",
    ),
    "codex": (
        "https://github.com/openai/codex/releases/download/rust-v0.165.0/"
        "codex-npm-linux-x64-0.165.0.tgz",
        "f997cd6ef5987126e19cd3c82e847a4a6461270f32f97340c5e99a65fb6f9b8a",
    ),
}
PACKAGES = """bubblewrap bison flex m4 build-essential perl git curl ca-certificates xz-utils
libasound2t64 libatk1.0-0t64 libatk-bridge2.0-0t64 libatspi2.0-0t64 libcairo2 libcups2t64
libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 libnspr4 libnss3 libpango-1.0-0 libx11-6
libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2
libxshmfence1 libxtst6 libxss1 libgtk-3-0t64 fonts-liberation xvfb""".split()


def sha(path: Path) -> str:
    """Return a streaming SHA-256 digest of one file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Qualification:
    """Keep provisioning logs separate from bulky, append-only runner outputs."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.evidence = root / "evidence"
        self.evidence.mkdir(parents=True, exist_ok=False)
        (root / "logs").mkdir()
        self.commands: list[dict[str, Any]] = []
        self.environment = os.environ.copy()
        self.environment["DEBIAN_FRONTEND"] = "noninteractive"
        self.secrets = [
            value
            for key, value in os.environ.items()
            if len(value) >= 8
            and any(part in key.upper() for part in ("TOKEN", "PASSWORD", "SECRET", "API_KEY"))
        ]

    def redact(self, text: str) -> str:
        """Remove inherited secret values without recording the host environment."""
        for value in self.secrets:
            text = text.replace(value, "[redacted]")
        return text

    def save(self, path: Path, value: Any) -> None:
        """Persist inspectable JSON with inherited secret values removed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.redact(json.dumps(value, indent=2)) + "\n")

    def run(self, name: str, argv: list[str]) -> str:
        """Execute one serial command and retain bounded diagnostics, status and identity."""
        print(f"{name}: starting", flush=True)
        log = self.root / "logs" / f"{len(self.commands):02d}-{name}.log"
        started = time.monotonic()
        with log.open("wb") as output:
            result = subprocess.run(
                argv, cwd=REPOSITORY, env=self.environment, stdout=output, stderr=subprocess.STDOUT
            )
        with log.open("rb") as stream:
            stream.seek(max(0, log.stat().st_size - 2 * 1024**2))
            diagnostic = self.redact(stream.read().decode(errors="replace"))
        target = self.evidence / log.name
        target.write_text(diagnostic)
        self.commands.append(
            {
                "name": name,
                "argv": argv,
                "returncode": result.returncode,
                "elapsed_seconds": time.monotonic() - started,
                "raw_log_sha256": sha(log),
                "raw_log_bytes": log.stat().st_size,
                "log": target.name,
                "log_truncated": log.stat().st_size > 2 * 1024**2,
            }
        )
        self.save(self.evidence / "commands.json", self.commands)
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode:
            print(diagnostic[-8000:], flush=True)
            raise RuntimeError(f"{name} failed with exit {result.returncode}; see {target.name}")
        return diagnostic.strip()

    def archive(self, name: str, tools: Path) -> None:
        """Verify pinned official archive bytes before safe extraction into a private root."""
        url, expected = ARCHIVES[name]
        archive = tools / f"{name}.tar"
        self.run(
            f"download-{name}",
            [
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--max-time",
                "600",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--output",
                str(archive),
                url,
            ],
        )
        if sha(archive) != expected:
            raise ValueError(f"{name} archive SHA-256 does not match the pinned release")
        with tarfile.open(archive) as stream:
            stream.extractall(tools / name, filter="data")

    def collect(self) -> None:
        """Copy only controller receipts, excluding all source, cache, build and auth trees."""
        patterns = (
            "prepared/*.json",
            "prepared/*/preparation.json",
            "runtime/*.json",
            "runtime/native/*.json",
            "runtime/resources/*.json",
            "dependencies/*/*.json",
            "qualification/report.json",
            "qualification/*/*.json",
            "qualification/*/*/*.json",
        )
        index = {}
        for pattern in patterns:
            for source in sorted(self.root.glob(pattern)):
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"unsafe receipt: {source}")
                relative = source.relative_to(self.root)
                exported = self.evidence / "receipts" / relative
                self.save(exported, json.loads(source.read_text()))
                index[str(relative)] = {
                    "source_sha256": sha(source),
                    "source_bytes": source.stat().st_size,
                    "exported_sha256": sha(exported),
                    "exported_bytes": exported.stat().st_size,
                }
        self.save(self.evidence / "receipt-index.json", index)


def main() -> int:
    """Run the existing four-case CLI serially and preserve partial evidence on failure."""
    root = Path(os.environ["RUNNER_TEMP"]).resolve() / "large-project-qualification"
    run = Qualification(root)
    provenance: dict[str, Any] = {
        "code_sha": os.environ.get("GITHUB_SHA"),
        "platform": platform.platform(),
        "driver_sha256": sha(Path(__file__)),
        "archives": ARCHIVES,
        "model_calls": 0,
        "status": "in_progress",
        "per_case_seconds": 1800,
    }
    run.save(run.evidence / "provenance.json", provenance)
    try:
        if platform.system() != "Linux" or platform.machine() != "x86_64":
            raise ValueError("qualification requires Linux x86_64")
        if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
            raise ValueError("qualification requires cgroup v2")
        free = shutil.disk_usage(root).free
        provenance["initial_free_disk_bytes"] = free
        if free < 20 * 1024**3:
            raise ValueError(
                "qualification requires at least 20 GiB free disk; no cleanup attempted"
            )
        sys.path.insert(0, str(REPOSITORY))
        from benchmarks.large_projects.native import package_identity
        from benchmarks.large_projects.resources import IMAGE
        from benchmarks.large_projects.runner import harness_hashes

        provenance["runner_hashes"] = harness_hashes()
        provenance["resource_image"] = IMAGE
        run.save(run.evidence / "provenance.json", provenance)
        run.run("apt-update", ["sudo", "-n", "apt-get", "update"])
        run.run("apt-install", ["sudo", "-n", "apt-get", "install", "-y", *PACKAGES])
        run.run("docker-info", ["docker", "info", "--format", "{{.CgroupVersion}} {{.OSType}}"])
        run.run("resource-image", ["docker", "pull", IMAGE])
        tools = root / "tools"
        tools.mkdir()
        for name in ARCHIVES:
            run.archive(name, tools)
        go = tools / "go/go"
        node = tools / "node/node-v22.22.1-linux-x64"
        package = tools / "codex/package/vendor/x86_64-unknown-linux-musl"
        codex = package / "bin/codex"
        provenance["native_package"] = package_identity(codex)
        run.environment["PATH"] = f"{go}/bin:{node}/bin:" + run.environment["PATH"]
        provenance["versions"] = {
            name: run.run(f"version-{name}", command)
            for name, command in (
                ("python", [sys.executable, "--version"]),
                ("codex", [str(codex), "--version"]),
                ("go", [str(go / "bin/go"), "version"]),
                ("node", [str(node / "bin/node"), "--version"]),
                ("npm", [str(node / "bin/npm"), "--version"]),
                ("bison", ["bison", "--version"]),
                ("flex", ["flex", "--version"]),
                ("cc", ["cc", "--version"]),
                ("make", ["make", "--version"]),
                ("bubblewrap", ["bwrap", "--version"]),
            )
        }
        run.save(run.evidence / "provenance.json", provenance)
        cli = [sys.executable, "-m", "benchmarks", "large"]
        prepared, dependencies = root / "prepared", root / "dependencies"
        run.run("prepare", [*cli, "prepare", "--output", str(prepared)])
        run.run(
            "runtime",
            [*cli, "runtime-check", "--codex", str(codex), "--output", str(root / "runtime")],
        )
        for case, toolchain in (
            ("otel-queue-cancellation", go),
            ("vscode-snippet-selections", node),
        ):
            run.run(
                f"prefetch-{case}",
                [
                    *cli,
                    "prefetch",
                    "--case",
                    case,
                    "--curator",
                    str(prepared / case),
                    "--toolchain",
                    str(toolchain),
                    "--seconds",
                    "1800",
                    "--output",
                    str(dependencies / case),
                ],
            )
        run.run(
            "qualify",
            [
                *cli,
                "qualify",
                "--prepared",
                str(prepared),
                "--output",
                str(root / "qualification"),
                "--dependencies",
                str(dependencies),
                "--toolchain",
                str(go),
                "--toolchain",
                str(node),
                "--seconds",
                "1800",
            ],
        )
        provenance["status"] = "passed"
    except (OSError, ValueError, RuntimeError, tarfile.TarError) as exc:
        provenance.update(status="failed", error=str(exc))
        print(f"Qualification failed: {run.redact(str(exc))}", file=sys.stderr, flush=True)
    finally:
        try:
            run.collect()
        except (OSError, ValueError) as exc:
            provenance.update(status="failed", evidence_error=str(exc))
        run.save(run.evidence / "provenance.json", provenance)
    return 0 if provenance["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
