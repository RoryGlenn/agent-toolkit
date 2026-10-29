"""Preview contact CSV files locally without importing or sending data."""

import argparse
import csv
import json
from pathlib import Path
import sys


def main() -> int:
    """Validate a CSV file and print its preview summary.

    Returns
    -------
    int
        Zero for a valid preview, or two for an invalid input.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--preview", action="store_true", required=True)
    args = parser.parse_args()
    try:
        with args.input.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not {"name", "email"}.issubset(reader.fieldnames or []):
                raise ValueError("CSV header must include name,email")
            rows = list(reader)
            for number, row in enumerate(rows, start=2):
                if not (row.get("email") or "").strip():
                    raise ValueError(f"Missing email on CSV line {number}")
            addresses = [row["email"].strip().casefold() for row in rows]
        print(json.dumps({"preview": True, "rows": len(rows),
                          "duplicate_emails": len(addresses) - len(set(addresses))}))
        return 0
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
