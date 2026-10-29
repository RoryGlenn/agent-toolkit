"""Export only pinned broken Git trees, never curator worktrees or caches."""

from __future__ import annotations

import io
import os
import tarfile
from pathlib import Path
from typing import Any

from benchmarks.large_projects.prepare import git


def export_parent(case: dict[str, Any], curator: Path, destination: Path) -> dict[str, Any]:
    """Stage source without history and without the evaluator's added tests.

    This produces input for a future isolated actor, not permission to execute it.
    Current comparison planning intentionally does not accept these cases.
    """
    destination.mkdir(parents=True, exist_ok=False)
    archive = git(curator / "repository", "archive", "--format=tar", case["parent"])
    total = 0
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        members = source.getmembers()
        for member in members:
            path = Path(member.name)
            total += member.size
            if (
                path.is_absolute()
                or ".." in path.parts
                or ".git" in path.parts
                or not (member.isfile() or member.isdir() or member.issym())
                or total > 1024**3
                or len(members) > 200_000
            ):
                raise ValueError("unsafe or oversized source archive")
            if member.issym():
                target = path.parent / member.linkname
                resolved = Path(os.path.normpath(target))
                if target.is_absolute() or ".." in resolved.parts:
                    raise ValueError("source symlink escapes the snapshot")
        links = {Path(member.name) for member in members if member.issym()}
        if any(any(parent in links for parent in Path(member.name).parents) for member in members):
            raise ValueError("archive member traverses a source symlink")
        # Extract files before links: no archive member can redirect subsequent writes.
        for member in sorted(members, key=lambda entry: entry.issym()):
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = source.extractfile(member)
                if stream is None:
                    raise ValueError("missing archive file")
                with target.open("xb") as output:
                    output.write(stream.read())
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(member.linkname)
    for member in members:
        if member.issym():
            resolved = (destination / member.name).resolve()
            if not resolved.is_relative_to(destination.resolve()):
                raise ValueError("chained source symlink escapes the snapshot")
    (destination / "TASK.md").write_text(case["task"] + "\n")
    return {
        "case_id": case["id"],
        "source_only": True,
        "candidate_execution_enabled": False,
        "files": len(members),
    }


if __name__ == "__main__":
    raise SystemExit("Use the large-project CLI export operation")
