"""Original small, adequately protected helper for the negative control."""

import unittest


def label(name: str) -> str:
    return "Item: " + name.strip()


class LabelTests(unittest.TestCase):
    def test_trimmed_name(self) -> None:
        self.assertEqual(label("  rope  "), "Item: rope")

    def test_empty_name(self) -> None:
        self.assertEqual(label(""), "Item: ")


if __name__ == "__main__":
    unittest.main()
