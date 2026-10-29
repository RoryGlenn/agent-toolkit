#!/usr/bin/env python3
"""Retrieve a personal A Philosophy of Software Design EPUB without external services."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import posixpath
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_DATA = Path.home() / ".local/share/software-design-specialist"
SCHEMA = "software-design-local-reference/v1"
TITLE = "A Philosophy of Software Design, 2nd Edition"
BLOCKS = {"p", "pre", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}


def digest(path: Path) -> str:
    """Return a file's SHA-256 fingerprint without loading it all into memory."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def member_path(base: str, relative: str) -> str:
    """Resolve an EPUB member reference while rejecting external or escaping paths."""
    if not relative or ":" in relative or "\\" in relative or relative.startswith("/"):
        raise ValueError(f"Expected a relative EPUB member: {relative}")
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), relative))
    if result == ".." or result.startswith("../"):
        raise ValueError(f"EPUB member escapes the archive: {relative}")
    return result


def render_text(element: ET.Element, member: str) -> str:
    """Keep literal whitespace and block boundaries, and identify original images.

    Parameters
    ----------
    element : Element
        Source XHTML node, interpreted only as data.
    member : str
        Archive path used to resolve embedded image references.

    Returns
    -------
    str
        Plain text. CSS positioning is not reconstructed; original image locators
        remain available for visual inspection.
    """
    tag = element.tag.rsplit("}", 1)[-1]
    if tag in {"script", "style"}:
        return ""
    if tag == "img":
        image = member_path(member, element.attrib["src"])
        return f"[IMAGE {image} | {element.get('alt', '')}]"
    if tag == "br":
        return "\n"
    content = element.text or ""
    for child in element:
        content += render_text(child, member) + (child.tail or "")
    if tag == "sup":
        return f"^({content})"
    if tag == "sub":
        return f"_({content})"
    if tag in {"td", "th"}:
        return content + " | "
    return content + ("\n\n" if tag in BLOCKS else "")


def label(node: ET.Element) -> str:
    """Read a required NCX label without flattening child navigation entries."""
    text = node.find("{*}navLabel/{*}text")
    if text is None or not text.text:
        raise ValueError("NCX entry has no title")
    return " ".join(text.text.split())


def locator(node: ET.Element) -> str:
    """Read the exact internal locator from a required NCX content element."""
    content = node.find("{*}content")
    if content is None:
        raise ValueError("NCX entry has no content locator")
    reference = content.attrib["src"]
    member, separator, anchor = reference.partition("#")
    member = member_path("toc.ncx", member)
    if separator and not anchor:
        raise ValueError("NCX entry has an empty anchor")
    return member + (f"#{anchor}" if separator else "")


def extract(epub: Path) -> dict[str, Any]:
    """Index the supplied edition using its NCX and sibling paragraph headings.

    Parameters
    ----------
    epub : Path
        Local source archive in the supplied second-edition layout.

    Returns
    -------
    dict
        Validated chapter and section text, exact locators, and image fingerprints.
        Chapter entries contain full chapters; section entries stop before the
        next section heading, retaining every intervening paragraph.
    """
    chapters: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    assets: dict[str, str] = {}
    with zipfile.ZipFile(epub) as archive:
        package = ET.fromstring(archive.read("content.opf"))
        title = package.find(".//{http://purl.org/dc/elements/1.1/}title")
        author = package.find(".//{http://purl.org/dc/elements/1.1/}creator")
        if (
            title is None
            or title.text != TITLE
            or author is None
            or "Ousterhout" not in (author.text or "")
        ):
            raise ValueError("Expected A Philosophy of Software Design, 2nd Edition by Ousterhout")
        navigation = ET.fromstring(archive.read("toc.ncx")).find("{*}navMap")
        if navigation is None:
            raise ValueError("Expected an NCX navigation map")
        for chapter_node in navigation:
            match = re.fullmatch(r"(\d+):\s*(.+)", label(chapter_node))
            if match is None:
                continue
            number = int(match[1])
            member = locator(chapter_node)
            if member != f"OEBPS/part{number + 4:04d}.xhtml":
                raise ValueError(f"Unexpected chapter source: {member}")
            source = archive.read(member)
            body = ET.fromstring(source).find("{*}body")
            if body is None:
                raise ValueError(f"Chapter has no body: {member}")
            children = list(body)
            if not children or " ".join(children[0].itertext()).strip() != f"Chapter {number}":
                raise ValueError(f"Chapter number disagrees with its source: {member}")
            anchors = {child.get("id"): index for index, child in enumerate(children)}
            headings = chapter_node.findall("{*}navPoint")
            entries: list[tuple[str, str, int]] = []
            for section_node in headings:
                reference = locator(section_node)
                section_member, separator, anchor = reference.partition("#")
                heading = label(section_node)
                if (
                    section_member != member
                    or not separator
                    or anchor not in anchors
                    or not re.match(rf"{number}\.\d+\b", heading)
                    or section_node.findall("{*}navPoint")
                ):
                    raise ValueError(f"Invalid sibling section heading: {reference}")
                position = anchors[anchor]
                assert position is not None
                entries.append((reference, heading, position))
            positions = [entry[2] for entry in entries]
            if positions != sorted(set(positions)):
                raise ValueError(f"Section order or duplicate anchors are invalid: {member}")
            source_headings = [
                index
                for index, child in enumerate(children)
                if re.match(rf"{number}\.\d+\s", " ".join(child.itertext()).strip())
            ]
            if source_headings != positions:
                raise ValueError(f"NCX omits or misidentifies a source section: {member}")
            full_text = render_text(body, member).strip()
            sections.append(
                {"chapter": number, "ref": member, "title": match[2], "text": full_text}
            )
            for index, (reference, heading, start) in enumerate(entries):
                end = entries[index + 1][2] if index + 1 < len(entries) else len(children)
                text = "".join(render_text(child, member) for child in children[start:end]).strip()
                if not text:
                    raise ValueError(f"Empty source section: {reference}")
                sections.append(
                    {"chapter": number, "ref": reference, "title": heading, "text": text}
                )
            for image in body.findall(".//{*}img"):
                image_member = member_path(member, image.attrib["src"])
                assets[image_member] = hashlib.sha256(archive.read(image_member)).hexdigest()
            chapters.append(
                {
                    "chapter": number,
                    "title": match[2],
                    "ref": member,
                    "words": len(full_text.split()),
                    "sections": len(entries),
                    "sha256": hashlib.sha256(source).hexdigest(),
                }
            )
    if [item["chapter"] for item in chapters] != list(range(1, 23)):
        raise ValueError("Expected all 22 chapters in order")
    return {
        "schema": SCHEMA,
        "title": TITLE,
        "source_sha256": digest(epub),
        "chapters": chapters,
        "sections": sections,
        "assets": assets,
    }


def load(data: Path) -> dict[str, Any]:
    """Load references only when both source fingerprint and full index are intact.

    Parameters
    ----------
    data : Path
        Personal library containing source.epub and index.json.

    Returns
    -------
    dict
        Verified source-derived corpus. Missing or modified data fails explicitly.
    """
    corpus: dict[str, Any] = json.loads((data / "index.json").read_text(encoding="utf-8"))
    if not isinstance(corpus, dict) or corpus.get("schema") != SCHEMA:
        raise ValueError("Unsupported local reference schema")
    if digest(data / "source.epub") != corpus["source_sha256"]:
        raise ValueError("Source fingerprint mismatch; references may be stale")
    if extract(data / "source.epub") != corpus:
        raise ValueError("Index differs from the source; do not trust its references")
    return corpus


def initialize(epub: Path, data: Path) -> None:
    """Create a stable local source and index, refusing conflicting existing files.

    Parameters
    ----------
    epub : Path
        User-supplied source archive.
    data : Path
        Personal library directory; other existing notes are preserved.
    """
    corpus = extract(epub)
    if data.is_symlink():
        raise ValueError("Use a real personal reference directory, not a symlink")
    data.mkdir(parents=True, exist_ok=True)
    source, index = data / "source.epub", data / "index.json"
    if source.exists() or index.exists() or source.is_symlink() or index.is_symlink():
        if not (source.is_symlink() or index.is_symlink()) and source.is_file() and index.is_file():
            if load(data) == corpus:
                print("Already initialized; source and index unchanged.")
                return
        raise ValueError(
            "Existing source/index differs or is incomplete; preserve it before rebuild"
        )
    with tempfile.TemporaryDirectory(prefix="software-design-index-") as temporary:
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
        f"Indexed {len(corpus['chapters'])} chapters and {len(corpus['sections'])} source entries."
    )
    print(f"Local source: {source}\nSHA-256: {corpus['source_sha256']}")


def search(corpus: dict[str, Any], query: str, chapter: int | None, limit: int) -> list[Any]:
    """Rank source entries containing all query words, favoring concise heading matches.

    Parameters
    ----------
    corpus : dict
        Verified local reference index.
    query : str
        Literal search terms, not a regular expression.
    chapter : int or None
        Optional chapter restriction.
    limit : int
        Maximum number of results.

    Returns
    -------
    list
        Source locators and bounded excerpts, not full arguments.
    """
    terms = set(re.findall(r"\w+", query.casefold()))
    if not terms:
        raise ValueError("Search needs at least one word")
    matches = []
    for section in corpus["sections"]:
        if chapter is not None and section["chapter"] != chapter:
            continue
        text = section["text"]
        tokens = re.findall(r"\w+", (section["title"] + " " + text).casefold())
        if not terms.issubset(tokens):
            continue
        score = sum(min(tokens.count(term), 8) for term in terms) / math.sqrt(len(tokens) + 1)
        score += 2 * sum(term in section["title"].casefold() for term in terms)
        positions = [text.casefold().find(term) for term in terms]
        start = max(0, min((p for p in positions if p >= 0), default=0) - 90)
        matches.append(
            (
                score,
                {
                    "ref": section["ref"],
                    "title": section["title"],
                    "chapter": section["chapter"],
                    "excerpt": text[start : start + 600],
                },
            )
        )
    return [entry for _, entry in sorted(matches, key=lambda item: item[0], reverse=True)[:limit]]


def read_section(corpus: dict[str, Any], reference: str, offset: int, limit: int) -> None:
    """Print a verified source entry with word pagination and explicit continuation.

    Parameters
    ----------
    corpus : dict
        Verified source-derived corpus.
    reference : str
        Exact locator returned by catalog or search.
    offset : int
        Zero-based starting word.
    limit : int
        Maximum words to print; intervening source whitespace is preserved.
    """
    section = next((item for item in corpus["sections"] if item["ref"] == reference), None)
    if section is None:
        raise ValueError("Use an exact source locator from catalog or search")
    rendered = section["text"]
    spans = list(re.finditer(r"\S+", rendered))
    if offset < 0 or offset >= len(spans) or not 1 <= limit <= 10000:
        raise ValueError(
            f"Offset must be within the {len(spans)}-word entry; words must be 1..10000"
        )
    end = min(len(spans), offset + limit)
    print(
        f"A Philosophy of Software Design, 2nd ed. | {reference} | "
        f"words {offset}:{end}/{len(spans)}"
    )
    print(rendered[spans[offset].start() : spans[end - 1].end()])
    if end < len(spans):
        print(f"\nCONTINUES: read --ref '{reference}' --offset {end} --words {limit}")


def extract_asset(data: Path, corpus: dict[str, Any], reference: str) -> Path:
    """Materialize an indexed image under a content-derived, local filename.

    Parameters
    ----------
    data : Path
        Personal reference library.
    corpus : dict
        Verified index containing original image fingerprints.
    reference : str
        Image member shown by a retrieved source entry.

    Returns
    -------
    Path
        Local image to inspect; existing differing files are never overwritten.
    """
    if reference not in corpus["assets"]:
        raise ValueError("Use an exact IMAGE locator from a retrieved chapter or section")
    suffix = posixpath.splitext(reference)[1].lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("Only indexed raster image assets can be materialized")
    with zipfile.ZipFile(data / "source.epub") as archive:
        image = archive.read(reference)
    fingerprint = hashlib.sha256(image).hexdigest()
    if fingerprint != corpus["assets"][reference]:
        raise ValueError("Image fingerprint mismatch")
    directory = data / "assets"
    if directory.is_symlink():
        raise ValueError("Asset directory must not be a symlink")
    directory.mkdir(exist_ok=True)
    target = directory / f"{fingerprint}{suffix}"
    if target.is_symlink():
        raise ValueError("Asset target must not be a symlink")
    if target.exists():
        if digest(target) != fingerprint:
            raise ValueError("Existing asset differs; preserve it before extracting again")
    else:
        with target.open("xb") as handle:
            handle.write(image)
    return target


def main() -> int:
    """Run the local reference CLI, returning a nonzero status on invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--epub", type=Path, required=True)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--chapter", type=int, choices=range(1, 23))
    find = commands.add_parser("search")
    find.add_argument("query")
    find.add_argument("--chapter", type=int, choices=range(1, 23))
    find.add_argument("--limit", type=int, default=6)
    read = commands.add_parser("read")
    read.add_argument("--ref", required=True)
    read.add_argument("--offset", type=int, default=0)
    read.add_argument("--words", type=int, default=1800)
    asset = commands.add_parser("asset")
    asset.add_argument("--ref", required=True)
    commands.add_parser("verify")
    args = parser.parse_args()
    try:
        data = args.data_dir.expanduser()
        if args.command == "init":
            initialize(args.epub.expanduser(), data)
            return 0
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
        elif args.command == "read":
            read_section(corpus, args.ref, args.offset, args.words)
        elif args.command == "asset":
            print(extract_asset(data, corpus, args.ref))
        else:
            print(f"Verified source SHA-256 and all {len(corpus['sections'])} indexed entries.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
