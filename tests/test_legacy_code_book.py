"""Exercise the Feathers helper using original synthetic EPUBs, never a private book."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "legacy_code_book", ROOT / "skills/legacy-code-skill/scripts/legacy_code.py"
)
assert SPEC is not None and SPEC.loader is not None
book = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(book)


def fixture(path: Path, transform: Callable[[str, str], str] | None = None) -> None:
    """Create original content with the supported nested NCX/XHTML structure."""
    members = {
        "META-INF/container.xml": '<container><rootfiles><rootfile full-path="book/package.opf"/>'
        "</rootfiles></container>",
        "book/figure.png": "original synthetic image bytes",
    }
    manifest, spine, nav = [], [], []
    for n in range(1, 26):
        name = f"ch{n:02}.xhtml"
        manifest.append(f'<item id="c{n}" href="{name}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="c{n}"/>')
        nav.append(
            f"<navPoint><navLabel><text>Chapter {n}: Fixture {n}</text></navLabel>"
            f'<content src="{name}"/></navPoint>'
        )
        techniques = ""
        if n == 25:
            techniques = "".join(
                f'<h3 id="ch25sec1lev{i}">Technique {i}</h3><p>Mechanism {i}.</p>'
                f'<div><h4 id="steps{i}">Steps</h4><p>Step for {i}.</p></div>'
                f"<p>Qualification for {i}.</p>"
                for i in range(1, 25)
            )
        members["book/" + name] = (
            f'<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Fixture {n}</title></head>'
            f'<body><h2 id="ch{n:02}">Chapter {n}: Fixture {n}</h2>'
            "<p>Introductory context is part of the chapter.</p>"
            '<div><h3 id="boundary">Dependency seam</h3>'
            "<p>Observe effects before replacing the dependency.</p>"
            '<p class="programlisting"><code>if ready:<br/>    emit()<br/>    save()</code></p>'
            "<p>Call vendor::send and the literal .* operator.</p>"
            "<table><tr><th>Input</th><th>Effect</th></tr><tr><td>1</td><td>Saved</td></tr></table>"
            '<p><img src="figure.png" alt="effect boundary"/></p>'
            '<h4 id="details">Nested detail</h4><p>Child qualification remains in its parent.</p>'
            "<p>Final parent qualification.</p></div>"
            '<h3 id="next">Separate topic</h3><p>The unrelated next argument.</p>'
            f"{techniques}</body></html>"
        )
    members["book/package.opf"] = (
        '<package xmlns:dc="http://purl.org/dc/elements/1.1/"><metadata>'
        f"<dc:title>{book.TITLE}</dc:title><dc:creator>Michael C. Feathers</dc:creator>"
        f"<dc:identifier>{book.ISBN}</dc:identifier></metadata><manifest>"
        '<item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        + "".join(manifest)
        + '</manifest><spine toc="toc">'
        + "".join(spine)
        + "</spine></package>"
    )
    members["book/toc.ncx"] = (
        "<ncx><navMap><navPoint><navLabel><text>Part</text></navLabel>"
        '<content src="ch01.xhtml"/>' + "".join(nav) + "</navPoint></navMap></ncx>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, transform(name, text) if transform else text)


class LegacyCodeBookTests(unittest.TestCase):
    """Check source integrity, complete semantic sections, privacy, and refusal behavior."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.epub, self.data = self.base / "fixture.epub", self.base / "private"
        fixture(self.epub)
        with contextlib.redirect_stdout(io.StringIO()):
            book.initialize(self.epub, self.data)

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["book.py", "--data-dir", str(self.data), *arguments]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = book.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def test_complete_chapters_and_heading_only_techniques(self) -> None:
        corpus = book.load(self.data)
        self.assertEqual([c["chapter"] for c in corpus["chapters"]], list(range(1, 26)))
        techniques = [s for s in corpus["sections"] if "#ch25sec1lev" in s["ref"]]
        self.assertEqual(len(techniques), 24)
        self.assertIn("Qualification for 24", techniques[-1]["text"])
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.data / "source.epub").stat().st_mode & 0o777, 0o600)

    def test_cli_entrypoint_loads_implementation_from_an_unrelated_directory(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills/legacy-code-skill/scripts/book.py"),
                "--data-dir",
                str(self.data),
                "verify",
            ],
            cwd=self.base,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Verified source SHA-256", result.stdout)

    def test_parent_includes_child_steps_and_excludes_next_technique(self) -> None:
        code, text, error = self.invoke("read", "--ref", "book/ch25.xhtml#ch25sec1lev1")
        self.assertEqual((code, error), (0, ""))
        self.assertIn("Step for 1.", text)
        self.assertIn("Qualification for 1.", text)
        self.assertNotIn("Technique 2", text)
        code, text, _ = self.invoke("read", "--ref", "book/ch25.xhtml#steps1")
        self.assertEqual(code, 0)
        self.assertIn("Qualification for 1", text)
        self.assertNotIn("Technique 2", text)

    def test_nested_sections_code_tables_images_and_intro_are_retained(self) -> None:
        code, text, _ = self.invoke("read", "--ref", "book/ch01.xhtml#boundary")
        self.assertEqual(code, 0)
        self.assertIn("if ready:\n    emit()\n    save()", text)
        self.assertIn("Input | Effect |", text)
        self.assertIn("1 | Saved |", text)
        self.assertIn("[IMAGE book/figure.png | effect boundary]", text)
        self.assertIn("Child qualification remains", text)
        self.assertIn("Final parent qualification", text)
        self.assertNotIn("unrelated next argument", text)
        _, chapter, _ = self.invoke("read", "--ref", "book/ch01.xhtml")
        self.assertIn("Introductory context", chapter)
        self.assertIn("unrelated next argument", chapter)

    def test_continuation_does_not_skip_the_final_qualification(self) -> None:
        code, first, _ = self.invoke("read", "--ref", "book/ch01.xhtml#boundary", "--words", "4")
        self.assertEqual(code, 0)
        self.assertIn("--offset 4 --words 4", first)
        code, rest, _ = self.invoke("read", "--ref", "book/ch01.xhtml#boundary", "--offset", "4")
        self.assertEqual(code, 0)
        self.assertIn("Final parent qualification", rest)

    def test_catalog_search_filters_and_invalid_requests(self) -> None:
        code, text, _ = self.invoke("catalog", "--chapter", "25")
        self.assertEqual(code, 0)
        self.assertTrue(any(s["ref"].endswith("#steps24") for s in json.loads(text)))
        code, text, _ = self.invoke("search", "dependency seam", "--chapter", "2", "--limit", "1")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)[0]["ref"], "book/ch02.xhtml#boundary")
        self.assertEqual(json.loads(self.invoke("search", "notaword")[1]), [])
        for arguments in [
            ("read", "--ref", "book/ch01.xhtml#unknown"),
            ("read", "--ref", "book/ch01.xhtml", "--words", "0"),
            ("read", "--ref", "book/ch01.xhtml", "--offset", "-1"),
            ("search", "   "),
            ("search", "word", "--limit", "51"),
        ]:
            with self.subTest(arguments=arguments):
                self.assertEqual(self.invoke(*arguments)[0], 1)

    def test_literal_search_preserves_phrase_order_and_code_punctuation(self) -> None:
        self.assertEqual(json.loads(self.invoke("search", "seam replacing")[1]), [])
        self.assertEqual(json.loads(self.invoke("search", "seam dependency")[1]), [])
        self.assertEqual(json.loads(self.invoke("search", "vend.*send")[1]), [])
        for query in ["::", ".*", "DEPENDENCY SEAM"]:
            code, output, error = self.invoke("search", query, "--chapter", "2", "--limit", "1")
            self.assertEqual((code, error), (0, ""))
            found = json.loads(output)
            self.assertEqual(len(found), 1)
            self.assertIn(query.casefold(), (found[0]["title"] + found[0]["excerpt"]).casefold())

    def test_permissive_existing_library_and_cache_are_refused_without_chmod(self) -> None:
        original = (self.data / "index.json").read_bytes()
        self.data.chmod(0o755)
        self.assertIn("private directory", self.invoke("verify")[2])
        with self.assertRaisesRegex(ValueError, "private directory"):
            book.initialize(self.epub, self.data)
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o755)
        self.assertEqual((self.data / "index.json").read_bytes(), original)
        self.data.chmod(0o700)
        cache = self.data / "assets"
        cache.mkdir(mode=0o755)
        self.assertIn("private directory", self.invoke("asset", "--ref", "book/figure.png")[2])
        self.assertEqual(cache.stat().st_mode & 0o777, 0o755)
        self.assertEqual(list(cache.iterdir()), [])

    def test_asset_is_private_at_initial_open_even_with_permissive_umask(self) -> None:
        opened_modes = []
        real_fdopen = os.fdopen

        def observe_open(descriptor: int, mode: str):  # type: ignore[no-untyped-def]
            opened_modes.append(os.fstat(descriptor).st_mode & 0o777)
            return real_fdopen(descriptor, mode)

        previous = os.umask(0)
        try:
            with patch.object(book.os, "fdopen", side_effect=observe_open):
                self.assertEqual(self.invoke("asset", "--ref", "book/figure.png")[0], 0)
        finally:
            os.umask(previous)
        self.assertEqual(opened_modes, [0o600])
        self.assertEqual((self.data / "assets").stat().st_mode & 0o777, 0o700)

    def test_source_and_complete_index_tampering_are_rejected(self) -> None:
        path = self.data / "index.json"
        original = path.read_bytes()
        for mutate in [
            lambda c: c["sections"][0].update(text="altered"),
            lambda c: c["sections"].pop(),
            lambda c: c["chapters"].pop(),
            lambda c: c["assets"].update({"book/figure.png": "wrong"}),
        ]:
            corpus = json.loads(original)
            mutate(corpus)
            path.write_text(json.dumps(corpus))
            for command in [
                ("verify",),
                ("search", "dependency"),
                ("read", "--ref", "book/ch01.xhtml"),
            ]:
                with self.subTest(command=command):
                    self.assertEqual(self.invoke(*command)[0], 1)
            path.write_bytes(original)
        with (self.data / "source.epub").open("ab") as handle:
            handle.write(b"changed source")
        self.assertIn("fingerprint mismatch", self.invoke("verify")[2])

    def test_idempotent_initialization_preserves_notes_and_refuses_incomplete_state(self) -> None:
        note = self.data / "notes.json"
        note.write_text('"private note"')
        original = {p.name: p.read_bytes() for p in self.data.iterdir() if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            book.initialize(self.epub, self.data)
        self.assertEqual(
            original, {p.name: p.read_bytes() for p in self.data.iterdir() if p.is_file()}
        )
        (self.data / "index.json").unlink()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            book.initialize(self.epub, self.data)
        self.assertEqual(note.read_text(), '"private note"')

    def test_failed_publish_rolls_back_only_its_own_files(self) -> None:
        data = self.base / "new"
        data.mkdir(mode=0o700)
        (data / "notes.txt").write_text("preserve")
        real_link = os.link

        def fail_second(source: Path, target: Path) -> None:
            if target.name == "index.json":
                raise OSError("simulated publish failure")
            real_link(source, target)

        with patch.object(book.os, "link", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "simulated"):
                book.initialize(self.epub, data)
        self.assertEqual([p.name for p in data.iterdir()], ["notes.txt"])

    def test_unsupported_and_incomplete_sources_never_publish(self) -> None:
        variants = [
            lambda n, s: s.replace(book.TITLE, "Unrelated book") if n.endswith(".opf") else s,
            lambda n, s: s.replace('<itemref idref="c12"/>', "") if n.endswith(".opf") else s,
            lambda n, s: s.replace("Chapter 12:", "Missing 12:") if n.endswith(".ncx") else s,
            lambda n, s: s.replace('id="ch01"', 'id="wrong"') if n.endswith("ch01.xhtml") else s,
            lambda n, s: (
                s.replace('id="ch25sec1lev24"', 'id="other"') if n.endswith("ch25.xhtml") else s
            ),
            lambda n, s: s.replace('id="next"', 'id="boundary"') if n.endswith("ch01.xhtml") else s,
        ]
        for i, transform in enumerate(variants):
            with self.subTest(i=i):
                source, data = self.base / f"bad{i}.epub", self.base / f"bad{i}"
                fixture(source, transform)
                with self.assertRaises((ValueError, KeyError)):
                    book.initialize(source, data)
                self.assertFalse(data.exists())

    def test_unsafe_links_assets_and_paths_preserve_outside_content(self) -> None:
        corpus = book.load(self.data)
        path = book.extract_asset(self.data, corpus, "book/figure.png")
        self.assertTrue(path.is_relative_to(self.data))
        self.assertEqual(path.read_bytes(), b"original synthetic image bytes")
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "differs"):
            book.extract_asset(self.data, corpus, "book/figure.png")
        outside = self.base / "outside"
        outside.mkdir()
        link = self.base / "linked"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "real directory"):
            book.initialize(self.epub, link / "library")
        self.assertEqual(list(outside.iterdir()), [])
        path.unlink()
        path.symlink_to(outside / "private")
        with self.assertRaises(ValueError):
            book.extract_asset(self.data, corpus, "book/figure.png")
        for reference in ["../../../escape", "/absolute", "https://example.test/a", "a\\b"]:
            with self.assertRaises(ValueError):
                book.member_path("book/ch01.xhtml", reference)
        self.assertEqual(book.member_path("book/html/a.xhtml", "../figure.png"), "book/figure.png")

    def test_source_operations_do_not_contact_network(self) -> None:
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            self.assertEqual(self.invoke("verify")[0], 0)
            self.assertEqual(self.invoke("search", "dependency")[0], 0)
            self.assertEqual(self.invoke("asset", "--ref", "book/figure.png")[0], 0)


if __name__ == "__main__":
    unittest.main()
