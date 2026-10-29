"""Freeze bounded production deltas without extracting a candidate-controlled archive.

The parent tree is immutable controller input. Build products, dependencies and candidate
tests never become evaluator inputs. Artifacts retain their identities as exclusions.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from benchmarks.files import hash_regular, read_regular, write_new_regular

SCOPES = {
    "cpython-import-locks": (
        "Lib/importlib/*.py",
        "Python/import*.c",
        "Include/internal/pycore_import*.h",
    ),
    "otel-queue-cancellation": ("exporter/exporterhelper/internal/queue/*.go",),
    "vscode-snippet-selections": ("src/vs/editor/contrib/snippet/browser/*.ts",),
    "postgres-tablespace-locking": (
        "src/backend/commands/*.c",
        "src/backend/catalog/*.c",
        "src/backend/storage/lmgr/*.c",
        "src/include/*.h",
    ),
}
MAX_DELTA = 64 * 1024**2
MAX_FILE = 8 * 1024**2


def production(case_id: str, name: str) -> bool:
    """The declared component scope excludes tests and build/evaluator entry points."""
    path = PurePosixPath(name)
    return (
        not any(part in {"test", "tests", ".git"} for part in path.parts)
        and not path.name.endswith("_test.go")
        and any(fnmatch.fnmatchcase(name, pattern) for pattern in SCOPES[case_id])
    )


def identity(path: Path) -> str:
    """Identify an immutable parent entry without following its links."""
    if path.is_symlink():
        return "symlink:" + os.readlink(path)
    return hash_regular(path, limit=512 * 1024**2)


def tree_hashes(root: Path) -> dict[str, str]:
    """Hash a controller-created tree, refusing directory links and special files."""
    if root.is_symlink():
        raise ValueError("symlink tree root rejected")
    result: dict[str, str] = {}
    total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            path = Path(directory) / name
            if path.is_symlink():
                files.append(name)
                dirs.remove(name)
        for name in sorted(files):
            path = Path(directory) / name
            total += path.lstat().st_size
            if total > 4 * 1024**3 or len(result) > 200_000:
                raise ValueError("source/dependency tree exceeds its inventory bound")
            result[str(path.relative_to(root))] = identity(path)
    return dict(sorted(result.items()))


def freeze_delta(
    case_id: str, archive: Path, parent: Path | dict[str, str], output: Path
) -> dict[str, Any]:
    """Read a paused cell's tar as data; never use extract/extractall on actor entries."""
    baseline = tree_hashes(parent) if isinstance(parent, Path) else parent
    output.mkdir(parents=True, exist_ok=False)
    files = output / "files"
    files.mkdir()
    seen: set[str] = set()
    excluded: dict[str, str] = {}
    changed: dict[str, str] = {}
    total = 0
    with tarfile.open(archive, mode="r|*") as stream:
        for index, member in enumerate(stream):
            parts = PurePosixPath(member.name).parts
            if (
                index > 200_000
                or not parts
                or member.name.startswith("/")
                or ".." in parts
                or member.size < 0
            ):
                raise ValueError("unsafe or excessive candidate archive")
            # docker cp names the selected directory as the archive's sole top level.
            if parts[0] != "workspace":
                raise ValueError("unexpected candidate archive root")
            if len(parts) == 1 or member.isdir():
                continue
            name = str(PurePosixPath(*parts[1:]))
            if name in seen:
                raise ValueError("duplicate candidate archive entry")
            seen.add(name)
            if any(
                part in {"node_modules", "out", ".build", ".benchmark-state", "__pycache__", ".git"}
                for part in parts[1:]
            ):
                continue
            if member.issym():
                value = "symlink:" + member.linkname
                if baseline.get(name) != value:
                    raise ValueError("candidate introduced or changed a source symlink")
                continue
            if not member.isfile() or member.islnk():
                raise ValueError("candidate artifact contains a nonregular source entry")
            content = stream.extractfile(member)
            if content is None:
                raise ValueError("missing candidate archive content")
            # Do not allocate or retain arbitrary build files; only declared source entries.
            accepted = production(case_id, name)
            if member.size > (MAX_FILE if accepted else 20_000_000):
                raise ValueError("candidate source file exceeds the artifact limit")
            if accepted:
                data = content.read(MAX_FILE + 1)
                value = hashlib.sha256(data).hexdigest()
            else:
                data = content.read(20_000_001)
                value = hashlib.sha256(data).hexdigest()
            if baseline.get(name) == value:
                continue
            total += len(data)
            if total > MAX_DELTA or len(changed) + len(excluded) >= 2000:
                raise ValueError("candidate source delta exceeds its bound")
            target = (files if accepted else output / "excluded") / name
            target.parent.mkdir(parents=True, exist_ok=True)
            write_new_regular(target, data)
            (changed if accepted else excluded)[name] = value
    deleted = sorted(name for name in baseline if name not in seen and production(case_id, name))
    manifest = {
        "case_id": case_id,
        "changed": changed,
        "deleted": deleted,
        "excluded_changes": excluded,
        "excluded_deletions": sorted(
            name for name in baseline if name not in seen and not production(case_id, name)
        ),
        "parent_fingerprint": fingerprint(baseline),
    }
    (output / "changes.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def fingerprint(value: Any) -> str:
    """Use the common structured provenance representation without a runtime import cycle."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def apply_delta(case_id: str, artifact: Path, parent: Path) -> dict[str, Any]:
    """Apply only verified ordinary source files to a fresh untouched parent export."""
    manifest: dict[str, Any] = json.loads(read_regular(artifact / "changes.json"))
    if manifest["case_id"] != case_id or manifest["parent_fingerprint"] != fingerprint(
        tree_hashes(parent)
    ):
        raise ValueError("candidate artifact belongs to another parent")
    for name in [*manifest["changed"], *manifest["deleted"]]:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or not production(case_id, name):
            raise ValueError("candidate artifact escapes the declared production scope")
        target = parent / name
        if any(p.is_symlink() for p in [target, *target.parents] if p != parent.parent):
            raise ValueError("candidate artifact traverses a parent symlink")
        if name in manifest["changed"]:
            data = read_regular(artifact / "files" / name)
            if hashlib.sha256(data).hexdigest() != manifest["changed"][name]:
                raise ValueError("candidate delta changed after freezing")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        else:
            target.unlink()
    return manifest
