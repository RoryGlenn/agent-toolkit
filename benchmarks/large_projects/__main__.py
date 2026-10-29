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
    runtime = sub.add_parser("runtime-check")
    runtime.add_argument("--codex", required=True, type=Path)
    runtime.add_argument("--output", required=True, type=Path)
    prep = sub.add_parser("prepare")
    prep.add_argument("--case", action="append", choices=[c["id"] for c in cases])
    prep.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("qualify")
    run.add_argument("--case", action="append", choices=[c["id"] for c in cases])
    run.add_argument("--prepared", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--toolchain", type=Path, action="append", default=[])
    run.add_argument("--seconds", type=int, default=7200)
    run.add_argument(
        "--dependencies",
        type=Path,
        help="root of separately prefetched per-case dependency bundles",
    )
    fetch = sub.add_parser("prefetch")
    fetch.add_argument("--case", required=True, choices=[c["id"] for c in cases])
    fetch.add_argument("--curator", type=Path, required=True)
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument("--toolchain", type=Path, action="append", default=[])
    fetch.add_argument("--seconds", type=int, default=1800)
    fetch.add_argument(
        "--chromium",
        type=Path,
        help="explicit preinstalled Chromium154 executable; no browser download",
    )
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
        elif args.operation == "runtime-check":
            from benchmarks.large_projects.qualification import qualify_runtime

            result = qualify_runtime(args.codex.resolve(strict=True), args.output.resolve())
            print(
                json.dumps(
                    {k: v for k, v in result.items() if k not in {"gates", "runner_hashes"}},
                    indent=2,
                )
            )
            if result["status"] != "passed":
                raise SystemExit(1)
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
                    args.dependencies / case["id"] if args.dependencies else None,
                )
                results.append(result)
                print(f"{case['id']}: {result['status']}", flush=True)
                if result["status"] == "cancelled":
                    attempted = {item["case_id"] for item in results}
                    results.extend(
                        {
                            "case_id": pending["id"],
                            "status": "not_started",
                            "ready_for_model_comparison": False,
                            "reason": "operator cancelled the qualification set",
                        }
                        for pending in cases
                        if pending["id"] not in attempted
                        and (not args.case or pending["id"] in args.case)
                    )
                    break
            (args.output / "report.json").write_text(json.dumps(results, indent=2) + "\n")
            if any(r["status"] == "cancelled" for r in results):
                raise SystemExit(130)
            if any(r["status"] != "qualified" for r in results):
                raise SystemExit(1)
        elif args.operation == "prefetch":
            from benchmarks.large_projects.integration import prefetch

            case = next(c for c in cases if c["id"] == args.case)
            result = prefetch(
                case, args.curator, args.output, args.toolchain, args.seconds, args.chromium
            )
            print(
                json.dumps(
                    {k: v for k, v in result.items() if k not in {"hashes", "commands"}}, indent=2
                )
            )
            if result["status"] != "prefetched":
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
            sides = ("parent", "fixed", "alternative", "partial")
            for side in (*sides, *(side + "-actor" for side in sides)):
                if (root / side).is_symlink():
                    raise ValueError("refusing symlink cleanup ancestor")
            # Keep all JSON receipts. Only known runner-owned bulky children are removed.
            for side in (*sides, *(side + "-actor" for side in sides)):
                for child in ("source", "build", "cache", "home", "tmp", "staging", "workspace"):
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
