"""Model-free large-project preparation, qualification, inspection and cleanup."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
from pathlib import Path

from benchmarks.large_projects.export import export_parent
from benchmarks.large_projects.prepare import CATALOG
from benchmarks.large_projects.runner import prepare_set, qualify


def main(argv: list[str] | None = None) -> None:
    """Expose curator operations without model credentials or comparison arms."""
    cases = json.loads(CATALOG.read_text())["cases"]
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("list")
    prep = sub.add_parser("prepare")
    prep.add_argument("--case", action="append", choices=[c["id"] for c in cases])
    prep.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("qualify")
    run.add_argument("--case", action="append", choices=[c["id"] for c in cases])
    run.add_argument("--prepared", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--toolchain", type=Path, action="append", default=[])
    run.add_argument("--seconds", type=int, default=7200)
    export = sub.add_parser("export")
    export.add_argument("--case", required=True, choices=[c["id"] for c in cases])
    export.add_argument("--curator", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    status = sub.add_parser("status")
    status.add_argument("directory", type=Path)
    clean = sub.add_parser("clean")
    clean.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.operation == "list":
            print(json.dumps(cases, indent=2))
        elif args.operation == "prepare":
            results = prepare_set(args.case or [c["id"] for c in cases], args.output)
            print(json.dumps(results, indent=2))
            if any(r.get("status") == "environment_failure" for r in results):
                raise SystemExit(1)
        elif args.operation == "qualify":
            if not 1 <= args.seconds <= 14400:
                raise ValueError("seconds must be 1..14400 per case")
            args.output.mkdir(parents=True, exist_ok=False)
            results = []
            for case in cases:
                if args.case and case["id"] not in args.case:
                    continue
                result = qualify(
                    case,
                    args.prepared / case["id"],
                    args.output / case["id"],
                    args.toolchain,
                    args.seconds,
                )
                results.append(result)
                print(f"{case['id']}: {result['status']}", flush=True)
            (args.output / "report.json").write_text(json.dumps(results, indent=2) + "\n")
            if any(r["status"] != "qualified" for r in results):
                raise SystemExit(1)
        elif args.operation == "export":
            case = next(c for c in cases if c["id"] == args.case)
            print(json.dumps(export_parent(case, args.curator, args.output), indent=2))
        elif args.operation == "status":
            for path in sorted(args.directory.glob("**/qualification.json")):
                # Inspect controller receipts only; never traverse copied project/cache trees.
                if "source" not in path.parts and "cache" not in path.parts:
                    value = json.loads(path.read_text())
                    print(f"{value['case_id']}: {value['status']} ({path})")
        elif args.operation == "clean":
            root = args.directory.absolute()
            if root.is_symlink() or not (root / "qualification.json").is_file():
                raise ValueError("clean requires a single qualification directory (no symlinks)")
            for side in ("parent", "fixed", "alternative", "partial"):
                if (root / side).is_symlink():
                    raise ValueError("refusing symlink cleanup ancestor")
            # Keep all JSON receipts. Only known runner-owned bulky children are removed.
            for side in ("parent", "fixed", "alternative", "partial"):
                for child in ("source", "build", "cache", "home", "tmp"):
                    path = root / side / child
                    if path.is_symlink():
                        raise ValueError("refusing symlink cleanup")
                    if path.is_dir():
                        # Go module caches intentionally make directories read-only.
                        # Walk only this owned tree and never follow directory symlinks.
                        for directory, _, _ in os.walk(path, followlinks=False):
                            owned = Path(directory)
                            if not owned.is_symlink():
                                owned.chmod(stat.S_IMODE(owned.stat().st_mode) | stat.S_IRWXU)
                        shutil.rmtree(path)
            print(f"Removed build/source/cache trees; evidence retained in {root}")
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f"large-project benchmark: {exc}\n")


if __name__ == "__main__":
    main()
