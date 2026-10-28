"""Exercise local reference integrity, retrieval, and installation without a real book."""

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
    "ddia_book", ROOT / "skills/ddia-specialist/scripts/book.py"
)
assert SPEC is not None and SPEC.loader is not None
book = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(book)


class BookTests(unittest.TestCase):
    """Check behavior with a minimal EPUB containing representative markup."""

    def setUp(self) -> None:
        """Build an isolated source with nested sections, math, and preformatted code."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.epub = self.base / "input.epub"
        self.data = self.base / "private"
        with zipfile.ZipFile(self.epub, "w") as archive:
            archive.writestr(
                "OEBPS/titlepage01.html",
                "<html><body>Designing Data-Intensive Applications Second Edition</body></html>",
            )
            for number in range(1, 15):
                archive.writestr(
                    f"OEBPS/ch{number:02d}.html",
                    f'<html><body><div id="chapter"><h1>Chapter {number}</h1>'
                    "<p>A title with <em>inline</em> text.</p>"
                    '<section id="skew"><h2>Write skew</h2>'
                    "<p>Snapshot isolation can permit write skew.</p>"
                    "<p>Precision is 2<sup>53</sup>; x<sub>1</sub> is a variable.</p>"
                    "<pre>if ready:\n    commit()\n</pre>"
                    '<section id="child"><h3>A qualification</h3>'
                    "<p>Assumptions must hold.</p></section></section></div></body></html>",
                )
        with contextlib.redirect_stdout(io.StringIO()):
            book.initialize(self.epub, self.data)

    def test_source_is_stable_and_search_has_real_locators(self) -> None:
        """Deleting the original does not break the local copy or grounded retrieval."""
        self.epub.unlink()
        corpus = book.load(self.data)
        matches = book.search(corpus, "write skew", 8, 3)
        self.assertEqual(matches[0]["ref"], "OEBPS/ch08.html#skew")
        self.assertEqual(matches[0]["chapter"], 8)
        self.assertEqual(book.search(corpus, "nonexistent concept", None, 6), [])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            book.read_section(self.data, matches[0]["ref"], 0, 1000)
        text = output.getvalue()
        self.assertIn("Assumptions must hold.", text)
        self.assertIn("2^(53)", text)
        self.assertIn("x_(1)", text)
        self.assertIn("if ready:\n    commit()", text)

    def test_pagination_is_explicit_and_invalid_anchors_fail(self) -> None:
        """Partial reads advertise continuation and cannot silently invent citations."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            book.read_section(self.data, "OEBPS/ch08.html#skew", 0, 4)
        self.assertIn("--offset 4", output.getvalue())
        for reference in ["OEBPS/ch08.html#missing", "../private#skew"]:
            with self.assertRaises(ValueError):
                book.read_section(self.data, reference, 0, 10)
        with self.assertRaises(ValueError):
            book.read_section(self.data, "OEBPS/ch08.html#skew", 10000, 10)

    def test_source_change_is_rejected(self) -> None:
        """A changed local EPUB cannot silently reuse stale references."""
        with (self.data / "source.epub").open("ab") as handle:
            handle.write(b"changed")
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            book.load(self.data)

    def test_verify_detects_index_change(self) -> None:
        """Re-extraction detects text tampering even when the source remains unchanged."""
        index = self.data / "index.json"
        corpus = json.loads(index.read_text())
        corpus["sections"][0]["text"] = "unsupported claim"
        index.write_text(json.dumps(corpus))
        with patch("sys.argv", ["book.py", "--data-dir", str(self.data), "verify"]):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(book.main(), 1)

    def test_repeat_initialize_preserves_existing_files(self) -> None:
        """Initialization is idempotent and refuses incomplete or conflicting storage."""
        before = (self.data / "index.json").stat().st_mtime_ns
        with contextlib.redirect_stdout(io.StringIO()):
            book.initialize(self.epub, self.data)
        self.assertEqual((self.data / "index.json").stat().st_mtime_ns, before)
        (self.data / "index.json").unlink()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            book.initialize(self.epub, self.data)

    def test_selected_install_and_restore(self) -> None:
        """The specialist's role and skill install together and restore cleanly."""
        home = self.base / "host"
        with contextlib.redirect_stdout(io.StringIO()):
            receipt = install.install(ROOT, "codex", ["ddia-specialist"], home, home / ".codex")
        assert receipt is not None
        role = home / ".codex/agents/ddia-specialist.toml"
        skill = home / ".agents/skills/ddia-specialist"
        self.assertFalse(role.is_symlink())
        self.assertTrue(role.samefile(ROOT / "agents/codex/ddia-specialist.toml"))
        self.assertEqual(skill.resolve(), ROOT / "skills/ddia-specialist")
        self.assertTrue((skill / "scripts/book.py").is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            install.restore(receipt)
        self.assertFalse(role.exists())
        self.assertFalse(skill.exists())


if __name__ == "__main__":
    unittest.main()
