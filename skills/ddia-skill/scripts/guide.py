#!/usr/bin/env python3
"""Route portable DDIA concepts and validate their coverage links."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddia-capabilities/v1"
WORKFLOWS = {"assess", "design", "review", "validate", "migrate", "operate", "explain"}


def load(root: Path = SKILL_ROOT) -> dict[str, Any]:
    """Load authored capability metadata from the installed shared skill."""
    data: dict[str, Any] = json.loads((root / "references/coverage.json").read_text())
    if data.get("schema") != SCHEMA:
        raise ValueError("Unsupported DDIA capability schema")
    return data


def local_file(root: Path, relative: str) -> Path:
    """Resolve a regular package resource without escaping through traversal or links."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Invalid package resource: {relative}")
    result = root / path
    for parent in (result, *result.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Linked package resource: {relative}")
    if not result.is_file() or not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing or external package resource: {relative}")
    return result


def concept_text(root: Path, concept: dict[str, Any]) -> str:
    """Read one concept section, preserving its worked examples and qualifications."""
    text = local_file(root, concept["reference"]).read_text()
    marker = f"## {concept['title']}\n"
    if text.count(marker) != 1:
        raise ValueError(f"Missing or duplicate concept section: {concept['id']}")
    return marker + text.split(marker, 1)[1].split("\n## ", 1)[0].strip() + "\n"


def route(
    query: str, root: Path = SKILL_ROOT, *, workflow: str | None = None, limit: int = 6
) -> list[dict[str, Any]]:
    """Rank topic references using query overlap; scores are routing, never evaluation."""
    terms = set(re.findall(r"\w+", query.casefold())) - {"a", "the", "and", "to", "for"}
    if not terms or not 1 <= limit <= 20:
        raise ValueError("Provide meaningful query terms and a limit from 1 to 20")
    matches = []
    for concept in load(root)["concepts"]:
        if workflow and workflow not in concept["workflows"]:
            continue
        title = set(re.findall(r"\w+", (concept["id"] + " " + concept["title"]).casefold()))
        body = set(re.findall(r"\w+", concept_text(root, concept).casefold()))
        score = len(terms & title) * 4 + len(terms & body)
        if score:
            matches.append((score, concept))
    matches.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [
        {key: concept[key] for key in ("id", "chapter", "title", "reference", "source_refs")}
        for _, concept in matches[:limit]
    ]


def check(root: Path = SKILL_ROOT, source_index: Path | None = None) -> dict[str, Any]:
    """Validate coverage, resource containment, workflow/case links and optional anchors.

    Parameters
    ----------
    root : Path
        Shared skill directory, including portable references and evaluations.
    source_index : Path, optional
        An explicitly selected original-source index; its fingerprint must match.

    Returns
    -------
    dict
        Mechanical validation counts. This is not an agent behavior evaluation.
    """
    data = load(root)
    cases = json.loads(local_file(root, "evals/cases.json").read_text())
    case_ids = {case["id"] for case in cases["cases"]}
    source_refs: set[str] | None = None
    if source_index is not None:
        index = json.loads(source_index.read_text())
        if index.get("source_sha256") != data["source_sha256"]:
            raise ValueError("Coverage source fingerprint differs from selected index")
        source_refs = {section["ref"] for section in index["sections"]}
    ids = set()
    chapters = set()
    for concept in data["concepts"]:
        ident = concept["id"]
        if not isinstance(ident, str) or ident in ids or not re.fullmatch(r"[a-z0-9-]+", ident):
            raise ValueError(f"Invalid or duplicate concept: {ident}")
        ids.add(ident)
        chapter = concept["chapter"]
        if type(chapter) is not int or not 1 <= chapter <= 14:
            raise ValueError(f"Invalid chapter: {chapter}")
        chapters.add(chapter)
        content = concept_text(root, concept)
        if not concept["workflows"] or set(concept["workflows"]) - WORKFLOWS:
            raise ValueError(f"Invalid workflow routes: {ident}")
        for workflow in concept["workflows"]:
            local_file(root, f"references/workflows/{workflow}.md")
        if not concept["evaluation_cases"] or set(concept["evaluation_cases"]) - case_ids:
            raise ValueError(f"Missing evaluation case: {ident}")
        if concept["status"] != {
            "guidance": "authored",
            "source_locators": "validated",
            "behavior": "not-measured",
        }:
            raise ValueError(f"Unexpected evidence claim; provide a versioned receipt: {ident}")
        if not concept["source_refs"]:
            raise ValueError(f"Missing source locators: {ident}")
        for reference in concept["source_refs"]:
            if not re.fullmatch(rf"OEBPS/ch{chapter:02d}\.html#[\w-]+", reference):
                raise ValueError(f"Invalid source locator: {reference}")
            if reference not in content or (
                source_refs is not None and reference not in source_refs
            ):
                raise ValueError(f"Unresolved source locator: {reference}")
    if chapters != set(range(1, 15)):
        raise ValueError("Coverage must route every substantive chapter")
    for case in cases["cases"]:
        if not case["concepts"] or set(case["concepts"]) - ids:
            raise ValueError(f"Case has unknown concepts: {case['id']}")
    return {
        "chapters": len(chapters),
        "concepts": len(ids),
        "cases": len(case_ids),
        "source_checked": source_refs is not None,
        "coverage_sha256": hashlib.sha256(
            local_file(root, "references/coverage.json").read_bytes()
        ).hexdigest(),
        "limits": "Resource/anchor validation only; no semantic or agent-competence claim.",
    }


def main() -> int:
    """Run a source-independent routing or coverage command."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    find = commands.add_parser("route")
    find.add_argument("query")
    find.add_argument("--workflow", choices=sorted(WORKFLOWS))
    find.add_argument("--limit", type=int, default=6)
    topics = commands.add_parser("topics")
    topics.add_argument("--chapter", type=int, choices=range(1, 15))
    show = commands.add_parser("concept")
    show.add_argument("id")
    validate = commands.add_parser("check")
    validate.add_argument("--source-index", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "route":
            result: Any = route(args.query, workflow=args.workflow, limit=args.limit)
        elif args.command == "check":
            result = check(source_index=args.source_index)
        else:
            concepts = load()["concepts"]
            if args.command == "concept":
                matches = [concept for concept in concepts if concept["id"] == args.id]
                if len(matches) != 1:
                    raise ValueError(f"Unknown concept: {args.id}")
                print(concept_text(SKILL_ROOT, matches[0]))
                return 0
            result = [c for c in concepts if args.chapter is None or c["chapter"] == args.chapter]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"DDIA guide: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
