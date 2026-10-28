"""Check sibling-heading EPUB retrieval and specialist installation with synthetic content."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import install

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "software_design_book", ROOT / "skills/software-design-specialist/scripts/book.py"
)
assert SPEC is not None and SPEC.loader is not None
book = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(book)


def fixture(path: Path, *, missing_anchor: bool = False, omit_section: bool = False) -> None:
    """Create a small original fixture with the source edition's paragraph structure.

    Parameters
    ----------
    path : Path
        Output ZIP path within a disposable test directory.
    missing_anchor : bool
        Make one NCX locator refer to a nonexistent source anchor.
    omit_section : bool
        Omit one source heading from the NCX to simulate an incomplete index input.
    """
    navigation = []
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "content.opf",
            '<package xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f"<metadata><dc:title>{book.TITLE}</dc:title>"
            "<dc:creator>John K. Ousterhout</dc:creator></metadata></package>",
        )
        for number in range(1, 23):
            member = f"OEBPS/part{number + 4:04d}.xhtml"
            anchor = "missing" if missing_anchor and number == 1 else "mechanism"
            second = (
                "<navPoint><navLabel><text>"
                f"{number}.2 Qualifications</text></navLabel>"
                f'<content src="{member}#qualification"/></navPoint>'
            )
            if omit_section and number == 1:
                second = ""
            navigation.append(
                f"<navPoint><navLabel><text>{number}: Topic {number}</text></navLabel>"
                f'<content src="{member}"/>'
                f"<navPoint><navLabel><text>{number}.1 Shared mechanism</text></navLabel>"
                f'<content src="{member}#{anchor}"/></navPoint>{second}</navPoint>'
            )
            archive.writestr(
                member,
                f"<html><body><p>Chapter {number}</p><p>Topic {number}</p>"
                "<p>Introductory framing matters.</p>"
                f'<p id="mechanism">{number}.1 Shared mechanism</p>'
                "<p>Hide shared decisions only when callers do not need them.</p>"
                "<pre>if ready:\n    perform_action()\n</pre>"
                "<p>Precision is 2<sup>53</sup> and x<sub>1</sub>.</p>"
                '<p><img src="diagram.png" alt="ownership boundary"/></p>'
                "<p>The final paragraph qualifies the first claim.</p>"
                f'<p id="qualification">{number}.2 Qualifications</p>'
                "<p>A distinct later section has separate obligations.</p></body></html>",
            )
        archive.writestr("toc.ncx", "<ncx><navMap>" + "".join(navigation) + "</navMap></ncx>")
        archive.writestr("OEBPS/diagram.png", b"synthetic image bytes; no book content")


class SoftwareDesignBookTests(unittest.TestCase):
    """Exercise full sections, exact citations, preserved input, and host integration."""

    def setUp(self) -> None:
        """Create a new local library for every test."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.epub = self.base / "fixture.epub"
        self.data = self.base / "private"
        fixture(self.epub)
        with contextlib.redirect_stdout(io.StringIO()):
            book.initialize(self.epub, self.data)

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        """Invoke the actual command dispatcher and capture its observable results.

        Parameters
        ----------
        arguments : str
            Command arguments following the private data-directory option.

        Returns
        -------
        tuple
            Exit status, stdout, and stderr.
        """
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["book.py", "--data-dir", str(self.data), *arguments]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = book.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def test_section_reads_all_siblings_and_stops_at_next_heading(self) -> None:
        """A paragraph-heading reference includes its body, qualifications, and code."""
        self.epub.unlink()
        status, text, error = self.invoke("read", "--ref", "OEBPS/part0014.xhtml#mechanism")
        self.assertEqual((status, error), (0, ""))
        self.assertIn("final paragraph qualifies", text)
        self.assertIn("if ready:\n    perform_action()", text)
        self.assertIn("2^(53)", text)
        self.assertIn("x_(1)", text)
        self.assertIn("[IMAGE OEBPS/diagram.png | ownership boundary]", text)
        self.assertNotIn("distinct later section", text)
        status, chapter, _ = self.invoke("read", "--ref", "OEBPS/part0014.xhtml")
        self.assertEqual(status, 0)
        self.assertIn("Introductory framing", chapter)
        self.assertIn("distinct later section", chapter)

    def test_pagination_continues_without_losing_body_content(self) -> None:
        """Small reads advertise an offset, and continuation reaches the concluding paragraph."""
        reference = "OEBPS/part0014.xhtml#mechanism"
        status, first, _ = self.invoke("read", "--ref", reference, "--words", "4")
        self.assertEqual(status, 0)
        self.assertIn("--offset 4 --words 4", first)
        status, remainder, _ = self.invoke("read", "--ref", reference, "--offset", "4")
        self.assertEqual(status, 0)
        self.assertIn("final paragraph qualifies", remainder)
        self.assertNotIn("CONTINUES:", remainder)
        for args in (("--offset", "-1"), ("--offset", "99999"), ("--words", "0")):
            self.assertEqual(self.invoke("read", "--ref", reference, *args)[0], 1)

    def test_catalog_and_search_return_actual_source_locators(self) -> None:
        """Catalog filters chapters and search requires all words within a source entry."""
        status, text, _ = self.invoke("catalog")
        self.assertEqual(status, 0)
        self.assertEqual([item["chapter"] for item in json.loads(text)], list(range(1, 23)))
        status, text, _ = self.invoke("catalog", "--chapter", "10")
        self.assertEqual(status, 0)
        self.assertEqual(len(json.loads(text)), 3)
        status, text, _ = self.invoke("search", "shared mechanism", "--chapter", "10")
        self.assertEqual(status, 0)
        matches = json.loads(text)
        self.assertEqual(matches[0]["ref"], "OEBPS/part0014.xhtml#mechanism")
        self.assertTrue(all(item["chapter"] == 10 for item in matches))
        self.assertEqual(json.loads(self.invoke("search", "shared nonexistent")[1]), [])
        self.assertEqual(self.invoke("search", "...")[0], 1)
        self.assertEqual(self.invoke("search", "shared", "--limit", "0")[0], 1)
        for reference in ("../private#mechanism", "OEBPS/part0014.xhtml#invented"):
            self.assertEqual(self.invoke("read", "--ref", reference)[0], 1)

    def test_tampered_index_is_rejected_by_search_read_and_verify(self) -> None:
        """A valid source hash cannot legitimize modified derived text or locators."""
        index = self.data / "index.json"
        corpus = json.loads(index.read_text())
        corpus["sections"][1]["text"] = "Unsupported fabricated claim."
        index.write_text(json.dumps(corpus))
        for args in (
            ("verify",),
            ("search", "fabricated"),
            ("read", "--ref", corpus["sections"][1]["ref"]),
        ):
            status, _, error = self.invoke(*args)
            self.assertEqual(status, 1)
            self.assertIn("Index differs", error)

    def test_source_change_and_incomplete_inputs_fail_explicitly(self) -> None:
        """Refuse stale data and incomplete table-of-contents references."""
        with (self.data / "source.epub").open("ab") as handle:
            handle.write(b"modified")
        status, _, error = self.invoke("verify")
        self.assertEqual(status, 1)
        self.assertIn("fingerprint mismatch", error)
        for name, options in (
            ("missing", {"missing_anchor": True}),
            ("omitted", {"omit_section": True}),
        ):
            epub = self.base / f"{name}.epub"
            fixture(epub, **options)
            with self.assertRaises(ValueError):
                book.extract(epub)

    def test_wrong_edition_and_missing_chapter_are_rejected(self) -> None:
        """Identity and complete chapter coverage are checked before publishing a library."""
        for name in ("wrong-title", "missing-chapter"):
            destination = self.base / f"{name}.epub"
            with zipfile.ZipFile(self.epub) as source, zipfile.ZipFile(destination, "w") as target:
                for member in source.namelist():
                    data = source.read(member)
                    if name == "wrong-title" and member == "content.opf":
                        data = data.replace(b"2nd Edition", b"1st Edition")
                    if name == "missing-chapter" and member == "OEBPS/part0026.xhtml":
                        continue
                    target.writestr(member, data)
            with self.assertRaises((ValueError, KeyError)):
                book.initialize(destination, self.base / name)
            self.assertFalse((self.base / name / "source.epub").exists())

    def test_repeat_initialization_preserves_notes_and_refuses_conflicts(self) -> None:
        """Idempotent import keeps study files and does not overwrite a broken installation."""
        notes = self.data / "notes.json"
        notes.write_text('{"private": "study"}')
        stamp = (self.data / "index.json").stat().st_mtime_ns
        self.assertEqual(self.invoke("init", "--epub", str(self.epub))[0], 0)
        self.assertEqual((self.data / "index.json").stat().st_mtime_ns, stamp)
        self.assertEqual(notes.read_text(), '{"private": "study"}')
        (self.data / "index.json").unlink()
        before = (self.data / "source.epub").read_bytes()
        self.assertEqual(self.invoke("init", "--epub", str(self.epub))[0], 1)
        self.assertEqual((self.data / "source.epub").read_bytes(), before)
        self.assertFalse((self.data / "index.json").exists())

    def test_assets_are_source_grounded_and_do_not_overwrite_changes(self) -> None:
        """Only known raster images are materialized and existing divergent content is preserved."""
        status, text, _ = self.invoke("asset", "--ref", "OEBPS/diagram.png")
        self.assertEqual(status, 0)
        image = Path(text.strip())
        self.assertTrue(image.is_relative_to(self.data))
        self.assertEqual(image.read_bytes(), b"synthetic image bytes; no book content")
        self.assertEqual(self.invoke("asset", "--ref", "OEBPS/diagram.png")[0], 0)
        image.write_bytes(b"existing user replacement")
        self.assertEqual(self.invoke("asset", "--ref", "OEBPS/diagram.png")[0], 1)
        self.assertEqual(image.read_bytes(), b"existing user replacement")
        self.assertEqual(self.invoke("asset", "--ref", "../outside.png")[0], 1)

    def test_selected_install_and_restore_preserve_other_roles(self) -> None:
        """A selected install supplies both real role and skill, then restores cleanly."""
        home = self.base / "host"
        other = home / ".codex/agents/other.toml"
        other.parent.mkdir(parents=True)
        other.write_text("unrelated user agent")
        with contextlib.redirect_stdout(io.StringIO()):
            receipt = install.install(
                ROOT, "codex", ["software-design-specialist"], home, home / ".codex"
            )
        assert receipt is not None
        role = home / ".codex/agents/software-design-specialist.toml"
        skill = home / ".agents/skills/software-design-specialist"
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(ROOT / "agents/codex/software-design-specialist.toml"))
        self.assertEqual(skill.resolve(), ROOT / "skills/software-design-specialist")
        self.assertTrue((skill / "scripts/book.py").is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            install.restore(receipt)
        self.assertFalse(role.exists())
        self.assertFalse(skill.exists())
        self.assertEqual(other.read_text(), "unrelated user agent")


if __name__ == "__main__":
    unittest.main()
