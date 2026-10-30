#!/usr/bin/env python3
"""Check authoring format and evidence inventory without claiming behavioral quality."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml  # type: ignore[import-untyped]

from install import ROOT, inventory

CATALOG = Path("standards/authoring/adoption.json")
SCHEMA = "agent-toolkit-authoring/v1"
STANDARD_VERSION = "1.1.0-proposed"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class UniqueLoader(yaml.SafeLoader):  # type: ignore[misc]
    """Reject duplicate YAML keys rather than silently replacing earlier values."""


def unique_mapping(loader: UniqueLoader, node: Any) -> dict[Any, Any]:
    """Construct a mapping whose keys are distinct and hashable."""
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key!r}")
            result[key] = loader.construct_object(value_node, deep=True)
        except TypeError as exc:
            raise ValueError("YAML mapping keys must be scalar values") from exc
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


@dataclass
class Report:
    """Collect structural diagnostics separately from behavioral assessment."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    covered_artifacts: int = 0
    behavior_assessment: str = "not_performed"


def frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Read safe, unambiguous YAML metadata and a nonempty Markdown body.

    Parameters
    ----------
    path : Path
        Skill or Markdown agent file.

    Returns
    -------
    tuple[dict[str, Any], str]
        Parsed metadata and remaining body.
    """
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)(.*)", text, re.DOTALL)
    if match is None:
        raise ValueError("Missing YAML frontmatter")
    data = yaml.load(match[1], Loader=UniqueLoader)
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise ValueError("Frontmatter must be a mapping with string keys")
    if not match[2].strip():
        raise ValueError("Instructions must not be empty")
    return data, match[2]


def check_skill(path: Path, report: Report) -> None:
    """Check portable skill fields; leave content judgments to semantic review."""
    try:
        data, _ = frontmatter(path)
        name = data.get("name")
        if (
            not isinstance(name, str)
            or len(name) > 64
            or NAME.fullmatch(name) is None
            or name != path.parent.name
        ):
            raise ValueError("Skill name must match its directory and use 1-64 valid characters")
        description = data.get("description")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            raise ValueError(
                "Skill description must be a nonempty string of at most 1024 characters"
            )
        for key in ("license", "compatibility", "allowed-tools"):
            if key in data and (not isinstance(data[key], str) or not data[key].strip()):
                raise ValueError(f"{key} must be a nonempty string when present")
        if len(data.get("compatibility", "")) > 500:
            raise ValueError("compatibility must not exceed 500 characters")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in metadata.items()
        ):
            raise ValueError("metadata must map string keys to string values")
        if len(path.read_text(encoding="utf-8").splitlines()) > 500:
            report.warnings.append(f"{path}: exceeds the recommended 500-line entrypoint ceiling")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report.errors.append(f"{path}: {exc}")


def existing_file(root: Path, value: Any) -> bool:
    """Return whether a canonical repository-relative path names a contained file."""
    if not isinstance(value, str) or not value:
        return False
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or str(relative) != value:
        return False
    path = root / value
    try:
        return path.resolve().is_relative_to(root.resolve()) and path.is_file()
    except (OSError, RuntimeError):
        return False


def check_catalog(root: Path, expected: set[str], report: Report) -> None:
    """Check exact artifact coverage and evidence locations, not their conclusions.

    Parameters
    ----------
    root : Path
        Toolkit checkout.
    expected : set[str]
        Complete set of shipped skill and role paths.
    report : Report
        Diagnostic accumulator.
    """
    try:
        data = json.loads((root / CATALOG).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError(f"Expected schema {SCHEMA}")
        if data.get("standard_version") != STANDARD_VERSION:
            raise ValueError(f"Expected standard_version {STANDARD_VERSION}")
        entries = data.get("artifacts")
        if not isinstance(entries, list):
            raise ValueError("artifacts must be a list")
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise ValueError("Every artifact must have a string path")
            path = entry["path"]
            if path in seen:
                raise ValueError(f"Duplicate artifact: {path}")
            seen.add(path)
            if not existing_file(root, path):
                report.errors.append(
                    f"Inventory artifact is missing or outside the checkout: {path}"
                )
            for key in ("basis", "next_check"):
                if not isinstance(entry.get(key), str) or not entry[key].strip():
                    report.errors.append(f"{path}: inventory needs a nonempty {key}")
            assessment = entry.get("assessment")
            if assessment not in ("not_assessed", "reviewed"):
                report.errors.append(
                    f"{path}: assessment must be not_assessed or reviewed, never a certification"
                )
            if assessment == "reviewed" and not existing_file(root, entry.get("review_record")):
                report.errors.append(f"{path}: reviewed entries need an existing review_record")
            evidence = entry.get("evidence")
            if not isinstance(evidence, list) or any(
                not existing_file(root, item) for item in evidence
            ):
                report.errors.append(f"{path}: evidence must list existing contained files")
        for path in sorted(expected - seen):
            report.errors.append(f"Missing adoption entry: {path}")
        for path in sorted(seen - expected):
            report.errors.append(f"Stale or unsupported adoption entry: {path}")
        report.covered_artifacts = len(seen & expected)
    except (OSError, ValueError) as exc:
        report.errors.append(f"{CATALOG}: {exc}")


def check(root: Path) -> Report:
    """Inspect a checkout without changing it or running model evaluations."""
    report = Report()
    try:
        inventory(root)
    except (OSError, ValueError) as exc:
        report.errors.append(f"Installer inventory: {exc}")
        return report
    paths = sorted((root / "skills").glob("*/SKILL.md"))
    for path in paths:
        check_skill(path, report)
    agents = sorted((root / "agents/codex").glob("*.toml"))
    agents += sorted((root / "agents/copilot").glob("*.agent.md"))
    for path in agents:
        if path.suffix == ".md":
            try:
                data, _ = frontmatter(path)
                if not isinstance(data.get("description"), str) or not data["description"].strip():
                    raise ValueError("Agent description must be a nonempty string")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                report.errors.append(f"{path}: {exc}")
    expected = {path.relative_to(root).as_posix() for path in paths + agents}
    check_catalog(root, expected, report)
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the read-only authoring CLI and return an error status for invalid structure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="Print a structured diagnostic report")
    args = parser.parse_args(argv)
    report = check(args.root.resolve())
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        for message in report.errors:
            print(f"ERROR: {message}")
        for message in report.warnings:
            print(f"WARNING: {message}")
        print(f"Authoring structure: {'invalid' if report.errors else 'valid'}")
        print(f"Inventoried artifacts: {report.covered_artifacts}")
        print(
            "Behavioral assessment: not performed; inspect evidence and review records separately."
        )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
