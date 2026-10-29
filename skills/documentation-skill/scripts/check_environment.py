"""Report documentation tooling without executing project code or changing files."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Any

TOOLS = (
    "git",
    "rg",
    "python3",
    "python",
    "node",
    "npm",
    "pnpm",
    "yarn",
    "bun",
    "uv",
    "vale",
    "markdownlint-cli2",
    "lychee",
    "pandoc",
    "pdftotext",
    "pdftoppm",
)
CONFIG_NAMES = {
    "AGENTS.md",
    "copilot-instructions.md",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    "pyproject.toml",
    "uv.lock",
    "poetry.lock",
    "requirements.txt",
    "mkdocs.yml",
    "mkdocs.yaml",
    "conf.py",
    ".vale.ini",
    ".markdownlint.json",
    ".markdownlint.jsonc",
    ".markdownlint.yaml",
    ".markdownlint.yml",
    ".markdownlint-cli2.jsonc",
    ".markdownlint-cli2.yaml",
    ".lychee.toml",
    "lychee.toml",
    ".nvmrc",
    ".node-version",
    ".python-version",
    "STYLE_GUIDE.md",
    "CONTRIBUTING.md",
}
CONFIG_PREFIXES = ("docusaurus.config.", "playwright.config.", "astro.config.")
EXCLUDED = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    "coverage",
    "site-packages",
    ".tox",
    "vendor",
}
MAX_FILE_BYTES = 1_048_576


def discover_files(root: Path, depth: int = 3) -> tuple[list[Path], list[str]]:
    """Find bounded configuration paths without following symlinks.

    Parameters
    ----------
    root : Path
        Existing project directory.
    depth : int
        Maximum relative directory depth.

    Returns
    -------
    tuple[list[Path], list[str]]
        Candidate paths and discovery limitations.
    """
    found: list[Path] = []
    warnings: list[str] = []

    def on_error(error: OSError) -> None:
        """Record a directory-read error without opening extra paths."""
        warnings.append(f"Could not scan a directory: {error.strerror}")

    for index, (folder, directories, filenames) in enumerate(os.walk(root, onerror=on_error)):
        if index >= 200:
            warnings.append("Stopped after 200 directories; inventory is partial.")
            break
        current = Path(folder)
        level = len(current.relative_to(root).parts)
        directories[:] = (
            sorted(
                name
                for name in directories
                if name not in EXCLUDED and not (current / name).is_symlink()
            )
            if level < depth
            else []
        )
        for name in sorted(filenames):
            if name not in CONFIG_NAMES and not name.startswith(CONFIG_PREFIXES):
                continue
            path = current / name
            if path.is_symlink():
                warnings.append(f"Skipped symlink: {path.relative_to(root).as_posix()}")
                continue
            found.append(path)
    return found, warnings


def find_package_manager(start: Path, root: Path) -> tuple[str | None, str]:
    """Find the nearest package-manager evidence within the selected project.

    Parameters
    ----------
    start : Path
        Directory containing the package being inspected.
    root : Path
        Explicit project boundary; ancestors above it are not inspected.

    Returns
    -------
    tuple[str | None, str]
        Manager and evidence location, or an explanation when unresolved.
    """
    current = start
    while current.is_relative_to(root):
        manifest = current / "package.json"
        if manifest.is_file() and not manifest.is_symlink():
            try:
                if manifest.stat().st_size <= MAX_FILE_BYTES:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    value = data.get("packageManager") if isinstance(data, dict) else None
                    manager = value.split("@", 1)[0] if isinstance(value, str) else None
                    if manager in {"npm", "pnpm", "yarn", "bun"}:
                        return manager, manifest.relative_to(root).as_posix()
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        locks = {
            tool
            for filename, tool in (
                ("pnpm-lock.yaml", "pnpm"),
                ("yarn.lock", "yarn"),
                ("bun.lock", "bun"),
                ("bun.lockb", "bun"),
                ("package-lock.json", "npm"),
                ("npm-shrinkwrap.json", "npm"),
            )
            if (current / filename).is_file() and not (current / filename).is_symlink()
        }
        if len(locks) == 1:
            return locks.pop(), f"lockfile in {current.relative_to(root).as_posix()}"
        if len(locks) > 1:
            return None, f"conflicting lockfiles in {current.relative_to(root).as_posix()}"
        if current == root:
            break
        current = current.parent
    return None, "no package-manager declaration or lockfile within selected project"


def inspect_manifest(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """List relevant npm-style script invocations without evaluating their bodies.

    Parameters
    ----------
    path : Path
        Package manifest path.
    root : Path
        Project root used for relative locations.

    Returns
    -------
    tuple[list[dict[str, Any]], list[str]]
        Suggested invocations and parse limitations.
    """
    label = path.relative_to(root).as_posix()
    try:
        if path.is_symlink() or not path.is_file():
            return [], [f"Skipped non-regular manifest: {label}"]
        if path.stat().st_size > MAX_FILE_BYTES:
            return [], [f"Skipped oversized manifest: {label}"]
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return [], [f"Expected an object in {label}"]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [], [f"Could not parse {label}: {type(error).__name__}"]
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return [], [f"Expected a scripts object in {label}"]
    manager, manager_evidence = find_package_manager(path.parent, root)
    commands = []
    for name, body in scripts.items():
        if not isinstance(body, str) or not isinstance(name, str):
            continue
        if not re.search(r"doc|lint|spell|link|preview|build|test", name, re.I):
            continue
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:_-]{0,99}", name):
            continue
        commands.append(
            {
                "source": label,
                "cwd": path.parent.relative_to(root).as_posix(),
                "script": name,
                "argv": [manager, "run", name] if manager else None,
                "package_manager_evidence": manager_evidence,
                "status": "discovered; inspect script and lifecycle hooks before running",
            }
        )
    return commands, []


def inspect_project(project: Path) -> dict[str, Any]:
    """Collect a read-only environment and documentation configuration inventory.

    Parameters
    ----------
    project : Path
        Existing project directory, supplied explicitly by the user.

    Returns
    -------
    dict[str, Any]
        JSON-compatible report without environment variable values or script bodies.

    Raises
    ------
    ValueError
        If the supplied project is not a directory.
    """
    root = project.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    paths, warnings = discover_files(root)
    commands: list[dict[str, Any]] = []
    for path in paths:
        if path.name == "package.json":
            additions, issues = inspect_manifest(path, root)
            commands.extend(additions)
            warnings.extend(issues)
    return {
        "project": str(root),
        "system": platform.system(),
        "python": {"path": sys.executable, "version": platform.python_version()},
        "tools": {name: shutil.which(name) for name in TOOLS},
        "configs": [p.relative_to(root).as_posix() for p in paths],
        "commands": commands,
        "warnings": warnings,
        "limits": [
            "No discovered executable or project script was run.",
            "Discovery is limited to depth 3 and 200 directories; "
            "missing entries are not proof of absence.",
            "Tools outside PATH, project-local node_modules/.bin, "
            "and remote environments may still be available.",
            "Review Python/doc-site configuration for additional project-specific commands.",
        ],
    }


def main() -> int:
    """Print the inventory and return a status code.

    Returns
    -------
    int
        Zero for a completed inventory or two for invalid input.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    args = parser.parse_args()
    try:
        report = inspect_project(args.project)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Project: {report['project']}\nPython: {report['python']['version']}")
        for tool, path in report["tools"].items():
            print(f"{tool}: {path or 'not found on PATH (optional)'}")
        print("\nConfigurations:")
        for path in report["configs"]:
            print(f"  {path}")
        print("\nDiscovered commands (not executed):")
        for command in report["commands"]:
            invocation = (
                " ".join(command["argv"])
                if command["argv"]
                else f"manager unresolved; script {command['script']}"
            )
            print(f"  [{command['cwd']}] {invocation}")
        for warning in report["warnings"] + report["limits"]:
            print(f"Note: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
