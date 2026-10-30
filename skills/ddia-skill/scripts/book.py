#!/usr/bin/env python3
"""Index and retrieve a personal DDIA EPUB locally using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_DATA = Path.home() / ".local/share/ddia-specialist"
SCHEMA = "ddia-local-reference/v1"
BLOCKS = {"p", "pre", "table", "dt", "dd", "figcaption"}
ALIASES = {
    "dedupe": "deduplication duplicate exactly once",
    "dedup": "deduplication duplicate exactly once",
    "idempotency": "idempotence duplicate request identity",
    "split brain": "leader failover fencing",
    "stale reads": "replication lag read writes",
    "hotspot": "hot spots skew",
    "backfill": "reprocessing migration derived data",
    "cdc": "change data capture",
    "2pc": "two phase commit",
    "2pl": "two phase locking",
    "ssi": "serializable snapshot isolation",
    "ann": "approximate nearest neighbor",
    "slo": "service level objective",
}
STOP_WORDS = {"a", "an", "and", "for", "how", "in", "is", "of", "the", "to", "with"}


def local_tag(element: ET.Element) -> str:
    """Return an XML element's local name without its namespace."""
    return element.tag.rsplit("}", 1)[-1]


def plain_text(element: ET.Element) -> str:
    """Normalize textual content while retaining separate inline element boundaries."""
    return re.sub(r"\s+", " ", render_text(element)).strip()


def render_text(element: ET.Element) -> str:
    """Retain code whitespace, block boundaries, and explicit superscript/subscript markers."""
    tag = local_tag(element)
    content = element.text or ""
    for child in element:
        content += render_text(child) + (child.tail or "")
    if tag == "sup":
        return f"^({content})"
    if tag == "sub":
        return f"_({content})"
    if tag in {"td", "th"}:
        return content + " | "
    if tag == "br":
        return "\n"
    if tag in BLOCKS | {"li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
        return content + "\n\n"
    return content


def digest(path: Path) -> str:
    """Compute a source fingerprint without loading its entire ZIP into memory."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def extract(epub: Path) -> dict[str, Any]:
    """Extract chapter text and exact heading anchors from the supplied second edition.

    Parameters
    ----------
    epub : Path
        Local EPUB archive. XML is parsed as data; no external links are fetched.

    Returns
    -------
    dict
        Source fingerprint, chapter inventories, and searchable heading fragments.
        Each fragment ends at the next heading; read retrieves a whole source section.
    """
    chapters: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    with zipfile.ZipFile(epub) as archive:
        title = plain_text(ET.fromstring(archive.read("OEBPS/titlepage01.html")))
        if "Second Edition" not in title or "Designing Data-Intensive Applications" not in title:
            raise ValueError("Expected the supplied DDIA Second Edition EPUB")
        for number in range(1, 15):
            member = f"OEBPS/ch{number:02d}.html"
            root = ET.fromstring(archive.read(member))
            parents = {child: parent for parent in root.iter() for child in parent}
            body = next(node for node in root.iter() if local_tag(node) == "body")
            current: dict[str, Any] | None = None
            chapter_sections: list[dict[str, Any]] = []

            def visit(
                node: ET.Element,
                parents: dict[ET.Element, ET.Element] = parents,
                member: str = member,
                number: int = number,
                chapter_sections: list[dict[str, Any]] = chapter_sections,
            ) -> None:
                """Collect ordered heading fragments, preserving code and table content."""
                nonlocal current
                tag = local_tag(node)
                if re.fullmatch(r"h[1-6]", tag):
                    container = node
                    while not container.get("id") and container in parents:
                        container = parents[container]
                    anchor = container.get("id")
                    if not anchor:
                        raise ValueError(f"Heading without source anchor: {member}")
                    current = {
                        "chapter": number,
                        "ref": f"{member}#{anchor}",
                        "title": plain_text(node),
                        "text": "",
                    }
                    chapter_sections.append(current)
                elif tag in BLOCKS:
                    if current is not None:
                        current["text"] += plain_text(node) + "\n\n"
                else:
                    for child in node:
                        visit(child)

            visit(body)
            if not chapter_sections:
                raise ValueError(f"No chapter headings found: {member}")
            for section in chapter_sections:
                section["text"] = section["text"].strip()
            sections.extend(chapter_sections)
            chapters.append(
                {
                    "chapter": number,
                    "title": chapter_sections[0]["title"],
                    "ref": chapter_sections[0]["ref"],
                    "words": len(plain_text(body).split()),
                    "headings": len(chapter_sections),
                    "sha256": hashlib.sha256(archive.read(member)).hexdigest(),
                }
            )
    return {
        "schema": SCHEMA,
        "source_sha256": digest(epub),
        "title": title,
        "chapters": chapters,
        "sections": sections,
    }


def initialize(epub: Path, data: Path) -> None:
    """Create a stable personal source and index without replacing existing data.

    Parameters
    ----------
    epub : Path
        User-supplied source archive.
    data : Path
        Local directory outside the toolkit repository.
    """
    corpus = extract(epub)
    data.mkdir(parents=True, exist_ok=True)
    source, index = data / "source.epub", data / "index.json"
    if source.exists() or index.exists():
        if source.is_file() and index.is_file() and load(data) == corpus:
            print("Already initialized; source and index unchanged.")
            return
        raise ValueError(
            "Existing source/index differs or is incomplete; preserve it before rebuild"
        )
    # Stage and validate before publishing either file. Exclusive creates avoid overwrites.
    with tempfile.TemporaryDirectory(prefix="ddia-index-") as temporary:
        staged = Path(temporary) / "source.epub"
        shutil.copyfile(epub, staged)
        if digest(staged) != corpus["source_sha256"]:
            raise ValueError("Source changed during indexing; retry with a stable EPUB")
        with source.open("xb") as target, staged.open("rb") as handle:
            shutil.copyfileobj(handle, target)
        with index.open("x", encoding="utf-8") as handle:
            json.dump(corpus, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(
        f"Indexed {len(corpus['chapters'])} chapters, {len(corpus['sections'])} heading fragments"
    )
    print(f"Local source: {source}\nSHA-256: {corpus['source_sha256']}")


def load(data: Path) -> dict[str, Any]:
    """Load an index only when its original source fingerprint still matches."""
    corpus: dict[str, Any] = json.loads((data / "index.json").read_text(encoding="utf-8"))
    if corpus.get("schema") != SCHEMA:
        raise ValueError("Unsupported local reference schema")
    if digest(data / "source.epub") != corpus["source_sha256"]:
        raise ValueError("Source fingerprint mismatch; references may be stale")
    return corpus


def search(corpus: dict[str, Any], query: str, chapter: int | None, limit: int) -> list[Any]:
    """Rank partial and alias matches, favoring original terms and exact headings.

    Search is an orientation aid, not evidence that a fragment supports a claim.
    Retrieve the full source section and relevant qualifications before attribution.
    """
    normalized = " ".join(re.findall(r"\w+", query.casefold()))
    terms = set(normalized.split()) - STOP_WORDS
    if not terms:
        raise ValueError("Search needs at least one word")
    expanded = set(terms)
    for phrase, expansion in ALIASES.items():
        if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", normalized):
            expanded.update(expansion.split())
    sections = [s for s in corpus["sections"] if chapter is None or s["chapter"] == chapter]
    documents = [
        set(re.findall(r"\w+", (s["title"] + " " + s["text"]).casefold())) for s in sections
    ]
    frequency = {term: sum(term in tokens for tokens in documents) for term in expanded}
    matches = []
    for section, document in zip(sections, documents, strict=True):
        text = section["text"]
        tokens = re.findall(r"\w+", (section["title"] + " " + text).casefold())
        matched = expanded & document
        if not matched:
            continue
        score = sum(
            math.log(1 + (len(sections) + 1) / (frequency[term] + 1))
            * (2 if term in terms else 0.5)
            * min(tokens.count(term), 3)
            / (1 + len(tokens) / 300)
            for term in matched
        )
        score += 6 * len(terms & document) / len(terms)
        score += 4 * sum(term in section["title"].casefold().split() for term in terms)
        score += 8 * (normalized in section["title"].casefold())
        positions = [text.casefold().find(term) for term in matched]
        start = max(0, min((p for p in positions if p >= 0), default=0) - 90)
        matches.append(
            (
                score,
                {
                    "ref": section["ref"],
                    "title": section["title"],
                    "chapter": section["chapter"],
                    "excerpt": text[start : start + 600],
                    "matched_terms": sorted(matched),
                },
            )
        )
    return [entry for _, entry in sorted(matches, key=lambda item: item[0], reverse=True)[:limit]]


def neighbors(corpus: dict[str, Any], reference: str) -> list[dict[str, Any]]:
    """Return nearby source locators so callers can inspect surrounding qualifications."""
    unique = list({section["ref"]: section for section in corpus["sections"]}.values())
    for index, section in enumerate(unique):
        if section["ref"] == reference:
            return [
                {key: entry[key] for key in ("ref", "title", "chapter")}
                for entry in unique[max(0, index - 2) : index + 3]
                if entry["chapter"] == section["chapter"]
            ]
    raise ValueError(f"Source reference not indexed: {reference}")


def read_section(data: Path, reference: str, offset: int, limit: int) -> None:
    """Print a source section with explicit word pagination and a stable EPUB locator."""
    member, separator, anchor = reference.partition("#")
    if not separator or not re.fullmatch(r"OEBPS/ch\d{2}\.html", member):
        raise ValueError("Use an exact OEBPS/chNN.html#anchor from catalog or search")
    with zipfile.ZipFile(data / "source.epub") as archive:
        root = ET.fromstring(archive.read(member))
        element = next((node for node in root.iter() if node.get("id") == anchor), None)
        if element is None:
            raise ValueError(f"Source anchor not found: {reference}")
        rendered = render_text(element).strip()
        spans = list(re.finditer(r"\S+", rendered))
    if offset >= len(spans):
        raise ValueError(f"Offset {offset} is past the {len(spans)}-word section")
    end = min(len(spans), offset + limit)
    print(f"DDIA 2nd ed. | {reference} | words {offset}:{end}/{len(spans)}")
    print(rendered[spans[offset].start() : spans[end - 1].end()])
    if end < len(spans):
        print(f"\nCONTINUES: read --ref '{reference}' --offset {end} --words {limit}")


def main() -> int:
    """Run local indexing, search, source retrieval, or integrity verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--epub", type=Path, required=True)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--chapter", type=int, choices=range(1, 15))
    find = commands.add_parser("search")
    find.add_argument("query")
    find.add_argument("--chapter", type=int, choices=range(1, 15))
    find.add_argument("--limit", type=int, default=6)
    read = commands.add_parser("read")
    read.add_argument("--ref", required=True)
    read.add_argument("--offset", type=int, default=0)
    read.add_argument("--words", type=int, default=1800)
    context = commands.add_parser("neighbors", help="Locate surrounding source qualifications.")
    context.add_argument("--ref", required=True)
    commands.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(args.epub.expanduser(), args.data_dir.expanduser())
            return 0
        data = args.data_dir.expanduser()
        corpus = load(data)
        if args.command == "catalog":
            entries = (
                corpus["chapters"]
                if args.chapter is None
                else [
                    {key: item[key] for key in ("ref", "title")}
                    for item in corpus["sections"]
                    if item["chapter"] == args.chapter
                ]
            )
            print(json.dumps(entries, ensure_ascii=False, indent=2))
        elif args.command == "search":
            if not 1 <= args.limit <= 50:
                raise ValueError("Limit must be between 1 and 50")
            print(
                json.dumps(
                    search(corpus, args.query, args.chapter, args.limit),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "neighbors":
            print(json.dumps(neighbors(corpus, args.ref), ensure_ascii=False, indent=2))
        elif args.command == "read":
            if args.offset < 0 or not 1 <= args.words <= 10000:
                raise ValueError("Offset must be nonnegative; words must be 1..10000")
            read_section(data, args.ref, args.offset, args.words)
        else:
            if extract(data / "source.epub") != corpus:
                raise ValueError("Index differs from the source; do not trust its search results")
            print(f"Verified source SHA-256 and all {len(corpus['sections'])} indexed fragments.")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        StopIteration,
        ET.ParseError,
        zipfile.BadZipFile,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
