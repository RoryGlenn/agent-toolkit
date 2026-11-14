"""Prepare answer-bearing upstream source controls, never candidate workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).with_name("catalog.json")
GIT_OPTIONS = [
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "filter.lfs.process=",
    "-c",
    "filter.lfs.smudge=cat",
    "-c",
    "filter.lfs.required=false",
]


def git(cwd: Path, *args: str, canonical_diff: bool = False) -> bytes:
    """Run a bounded curator Git command without hooks or LFS downloads.

    Parameters
    ----------
    cwd
        Command working directory.
    args
        Git arguments, passed without a shell.
    canonical_diff
        Ignore user/system diff configuration without changing fetch authentication.
    """
    env = os.environ.copy()
    if canonical_diff:
        for key in list(env):
            if key.startswith("GIT_CONFIG") or key in ("GIT_DIFF_OPTS", "GIT_EXTERNAL_DIFF"):
                del env[key]
        env.update(
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_ATTR_NOSYSTEM": "1",
                "LC_ALL": "C",
            }
        )
    process = subprocess.Popen(
        ["git", *GIT_OPTIONS, *args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=300)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    if process.returncode:
        raise RuntimeError(f"git {args[0]} failed: {stderr.decode(errors='replace')}")
    return stdout


def test_patch(repository: Path, parent: str, fixed: str, paths: list[str]) -> bytes:
    """Produce the canonical upstream test delta independent of ambient diff settings.

    Parameters
    ----------
    repository
        Fresh curator Git repository with pinned objects.
    parent, fixed
        Immutable source revisions.
    paths
        Exact trusted test paths from the catalog.

    Notes
    -----
    Full blob IDs avoid abbreviation differences in shallow object databases.
    Hunk function labels are informational and removed to avoid diff-driver heuristics.
    """
    patch = git(
        repository,
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.quotePath=true",
        "diff",
        "--binary",
        "--full-index",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--no-relative",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        "--diff-algorithm=myers",
        "--no-indent-heuristic",
        "--unified=3",
        "--inter-hunk-context=0",
        "--output-indicator-new=+",
        "--output-indicator-old=-",
        "--output-indicator-context= ",
        parent,
        fixed,
        "--",
        *paths,
        canonical_diff=True,
    )
    return re.sub(
        rb"^(@@ -[0-9]+(?:,[0-9]+)? \+[0-9]+(?:,[0-9]+)? @@)[^\n]*",
        rb"\1",
        patch,
        flags=re.MULTILINE,
    )


def prepare(case: dict[str, Any], destination: Path) -> dict[str, Any]:
    """Create pinned parent-plus-tests and fixed curator worktrees.

    Parameters
    ----------
    case
        Trusted catalog entry. Not a candidate-controlled input.
    destination
        A new directory; occupied paths are refused and never cleaned up.

    Returns
    -------
    dict
        Preparation receipt. It does not establish build or test success.
    """
    destination = destination.absolute()
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "CURATOR_ONLY.txt").write_text(
        "Contains reference answers and Git history. Not an isolated candidate workspace.\n"
        "Partial failures are retained for inspection.\n"
    )
    repository = destination / "repository"
    repository.mkdir()
    git(repository, "init", "-q", "--template=")
    git(repository, "remote", "add", "origin", case["url"])
    git(repository, "fetch", "--no-tags", "--depth=2", "origin", case["fixed"])
    actual_parent = git(repository, "rev-parse", f"{case['fixed']}^1").decode().strip()
    if actual_parent != case["parent"]:
        raise ValueError("Reference commit's direct parent does not match the catalog")
    patch = test_patch(repository, case["parent"], case["fixed"], case["test_paths"])
    patch_hash = hashlib.sha256(patch).hexdigest()
    if patch_hash != case["test_patch_sha256"]:
        raise ValueError("Upstream test patch does not match the catalog digest")
    patch_path = destination / "upstream-tests.patch"
    patch_path.write_bytes(patch)
    for side, revision in [("parent", case["parent"]), ("fixed", case["fixed"])]:
        git(repository, "worktree", "add", "--detach", str(destination / side), revision)
    git(destination / "parent", "apply", "--check", str(patch_path))
    git(destination / "parent", "apply", str(patch_path))
    receipt = {
        "case_id": case["id"],
        "parent": actual_parent,
        "fixed": case["fixed"],
        "test_patch_sha256": patch_hash,
        "workspace": str(destination),
        "source_preparation_only": True,
        "ready_for_model_comparison": False,
        "lfs": "Pointers retained; optional asset exclusions need case-specific validation.",
    }
    (destination / "preparation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> None:
    """Prepare one trusted case from the adjacent handoff catalog."""
    cases = json.loads(CATALOG.read_text())["cases"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=[case["id"] for case in cases])
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    case = next(case for case in cases if case["id"] == args.case)
    try:
        print(json.dumps(prepare(case, args.destination), indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Preparation failed; partial workspace retained: {exc}\n")


if __name__ == "__main__":
    main()
