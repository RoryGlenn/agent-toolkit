"""Descriptor-relative reads of untrusted artifacts; never follow candidate aliases."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

LIMIT = 20_000_000


def read_regular(path: Path) -> bytes:
    """Read a bounded, single-link regular file using no-follow directory descriptors."""
    absolute = path.absolute()
    descriptor = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in absolute.parts[1:-1]:
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = child
        child = os.open(
            absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        try:
            before = os.fstat(child)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > LIMIT:
                raise ValueError(f"unsafe file: {path.name}")
            chunks = []
            total = 0
            while chunk := os.read(child, 65536):
                total += len(chunk)
                if total > LIMIT:
                    raise ValueError("file exceeded size limit while reading")
                chunks.append(chunk)
            after = os.fstat(child)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("file changed while reading")
            return b"".join(chunks)
        finally:
            os.close(child)
    finally:
        os.close(descriptor)


def snapshot(root: Path) -> dict[str, bytes]:
    """Traverse through held directory descriptors, rejecting every alias and special file."""
    if root.is_symlink():
        raise ValueError("symlink artifact root rejected")
    root = root.resolve(strict=True)
    result: dict[str, bytes] = {}
    total = 0

    def visit(directory: int, prefix: Path) -> None:
        nonlocal total
        for name in sorted(os.listdir(directory)):
            relative = prefix / name
            metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                raise ValueError(f"symlink artifact rejected: {relative}")
            if name in {".codex", ".agents", ".git"}:
                raise ValueError(f"actor configuration artifact rejected: {relative}")
            if stat.S_ISDIR(metadata.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                )
                try:
                    visit(child, relative)
                finally:
                    os.close(child)
            elif stat.S_ISREG(metadata.st_mode):
                # read_regular independently walks no-follow descriptors, including parents.
                data = read_regular(root / relative)
                total += len(data)
                if total > LIMIT or len(result) >= 500:
                    raise ValueError("artifact size/file limit exceeded")
                result[str(relative)] = data
            else:
                raise ValueError("nonregular artifact rejected")

    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        visit(descriptor, Path())
    finally:
        os.close(descriptor)
    for name in ("recordbatch.py", "build.py", "README.md"):
        if name not in result:
            raise ValueError(f"required artifact missing: {name}")
    return result


def hashes(files: dict[str, bytes]) -> dict[str, str]:
    """Fingerprint the exact bytes obtained through safe descriptors."""
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def copy_snapshot(files: dict[str, bytes], destination: Path, *, fresh_state: bool = False) -> None:
    """Populate a new controller-owned directory before granting candidate access."""
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe snapshot path")
        if fresh_state and ("__pycache__" in relative.parts or ".sqlite" in relative.name):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)


def write_new_regular(path: Path, data: bytes) -> None:
    """Create a new file exclusively through no-follow parent directory descriptors."""
    absolute = path.absolute()
    descriptor = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in absolute.parts[1:-1]:
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = child
        child = os.open(
            absolute.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=descriptor,
        )
        with os.fdopen(child, "wb") as output:
            output.write(data)
    finally:
        os.close(descriptor)
