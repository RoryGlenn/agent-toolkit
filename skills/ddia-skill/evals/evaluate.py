#!/usr/bin/env python3
"""Freeze three-arm DDIA reasoning trials and collect evidence-based human review scores.

This planner does not execute models or enforce host isolation. Use separate fresh agent
sessions with only each actor directory exposed; record the same model and tool budget.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import statistics
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddia-comparison-plan/v1"
IGNORED = {"__pycache__", ".DS_Store", ".mypy_cache", ".ruff_cache", "node_modules"}


def digest(content: bytes) -> str:
    """Return a reproducible content fingerprint."""
    return hashlib.sha256(content).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    """Read a regular JSON object without following a supplied file symlink."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected regular JSON file: {path}")
    data: Any = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def inventory(directory: Path) -> dict[str, str]:
    """Fingerprint regular snapshot files and reject links or special files."""
    result = {}
    if directory.is_symlink():
        raise ValueError(f"Snapshot root is a symlink: {directory}")
    for path in sorted(directory.rglob("*")):
        if any(part in IGNORED for part in path.relative_to(directory).parts):
            continue
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError(f"Non-regular snapshot resource: {path}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = digest(path.read_bytes())
    return result


def snapshot_skill(source: Path, destination: Path) -> dict[str, str]:
    """Copy actor guidance while withholding evaluation prompts, rubrics and receipts."""
    if not source.is_dir() or source.is_symlink() or not (source / "SKILL.md").is_file():
        raise ValueError(f"Expected an explicit shared skill directory: {source}")
    for relative in inventory(source):
        if relative.split("/", 1)[0] == "evals":
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    catalog = source / "evals/cases.json"
    if catalog.is_file():
        data = read_json(catalog)
        # Retain link validation without exposing grading requirements to the actor.
        stripped = {
            "cases": [{"id": case["id"], "concepts": case["concepts"]} for case in data["cases"]]
        }
        target = destination / "evals/cases.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(stripped, indent=2) + "\n")
    return inventory(destination)


def cases(root: Path = SKILL_ROOT) -> list[dict[str, Any]]:
    """Load the public authored cases, which are not held-out or measured results."""
    data = read_json(root / "evals/cases.json")
    if data.get("schema") != "ddia-evaluation-cases/v1":
        raise ValueError("Unsupported evaluation case schema")
    result: list[dict[str, Any]] = data["cases"]
    ids = [case["id"] for case in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evaluation case IDs")
    return result


def plan(
    output: Path,
    current_skill: Path,
    redesigned_skill: Path,
    *,
    selected: list[str],
    trials: int,
    seed: int,
    model: str,
    effort: str,
    budget: str,
    source_library: Path | None = None,
) -> dict[str, Any]:
    """Freeze matched tasks/resources; refuse overwrites and source/output overlap.

    Parameters
    ----------
    output : Path
        New comparison directory. Existing paths are never overwritten.
    current_skill, redesigned_skill : Path
        Explicit guidance snapshots for the two specialist conditions.
    selected : list of str
        Case IDs, or an empty list for all public cases.
    trials : int
        Independent repetitions per case and arm, from one to twenty.
    seed : int
        Seed for arm execution order only, not a deterministic-system claim.
    model, effort, budget : str
        Fixed experiment settings to use in fresh host sessions.
    source_library : Path, optional
        Explicit source.epub/index.json pair exposed equally to both specialists.
    """
    if not 1 <= trials <= 20 or not all(item.strip() for item in (model, effort, budget)):
        raise ValueError("Trials must be 1..20; model, effort and budget must be explicit")
    catalog = cases()
    unknown = set(selected) - {case["id"] for case in catalog}
    if unknown:
        raise ValueError(f"Unknown cases: {sorted(unknown)}")
    chosen = [case for case in catalog if not selected or case["id"] in selected]
    output = output.absolute()
    for source in (current_skill, redesigned_skill, source_library):
        if source is not None:
            a, b = output.resolve(), source.resolve()
            if a.is_relative_to(b) or b.is_relative_to(a):
                raise ValueError("Comparison output and inputs must not overlap")
    library_fingerprint: dict[str, str] | None = None
    if source_library is not None:
        if source_library.is_symlink():
            raise ValueError("Source library must be a regular directory")
        index = read_json(source_library / "index.json")
        if index.get("schema") != "ddia-local-reference/v1":
            raise ValueError("Unsupported original-source library schema")
        ledger = redesigned_skill / "references/coverage.json"
        if ledger.is_file() and read_json(ledger).get("source_sha256") != index.get(
            "source_sha256"
        ):
            raise ValueError("Source library differs from redesigned guidance source")
        source = source_library / "source.epub"
        if source.is_symlink() or not source.is_file():
            raise ValueError("Missing regular source EPUB")
        if digest(source.read_bytes()) != index.get("source_sha256"):
            raise ValueError("Source library fingerprint mismatch")
        library_fingerprint = {
            name: digest((source_library / name).read_bytes())
            for name in ("source.epub", "index.json")
        }
    output.mkdir(parents=True, exist_ok=False)
    try:
        rng = random.Random(seed)
        runs = []
        for case in chosen:
            for trial in range(1, trials + 1):
                arms = ["baseline", "current", "redesigned"]
                rng.shuffle(arms)
                for arm in arms:
                    ident = f"{case['id']}-t{trial:02}-{arm}"
                    actor = output / "actors" / ident
                    actor.mkdir(parents=True)
                    rules = (
                        "Complete TASK.md in a fresh session. Use only this actor directory and "
                        "permitted general tools. Do not inspect other trials, arms, grader files, "
                        "personal skill/source libraries or prior responses. Do not mutate live "
                        "services. Distinguish actual execution from proposed checks.\n"
                    )
                    if arm != "baseline":
                        source = current_skill if arm == "current" else redesigned_skill
                        snapshot_skill(source, actor / "resources/ddia-skill")
                        rules += "Read resources/ddia-skill/SKILL.md and relevant resources.\n"
                        if source_library is not None:
                            destination = actor / "resources/source-library"
                            destination.mkdir()
                            for name in ("source.epub", "index.json"):
                                shutil.copyfile(source_library / name, destination / name)
                            rules += (
                                "Use only resources/source-library for original book retrieval; "
                                "pass its path with book.py --data-dir.\n"
                            )
                        else:
                            rules += "Original book source is not supplied; disclose that limit.\n"
                    (actor / "AGENTS.md").write_text(rules)
                    (actor / "TASK.md").write_text(case["prompt"] + "\n")
                    runs.append(
                        {
                            "id": ident,
                            "case": case["id"],
                            "trial": trial,
                            "arm": arm,
                            "actor": actor.relative_to(output).as_posix(),
                            "files": inventory(actor),
                        }
                    )
        result = {
            "schema": SCHEMA,
            "settings": {"model": model, "effort": effort, "budget": budget},
            "seed": seed,
            "trials": trials,
            "cases": chosen,
            "runs": runs,
            "source_library": library_fingerprint,
            "limits": "Public reasoning cases; planner does not enforce isolation, settings, "
            "execution or blinding. Use fresh sessions and independent reviewers. "
            "Hashes detect accidental changes, not hostile rewriting of the plan seal.",
        }
        content = json.dumps(result, indent=2).encode() + b"\n"
        (output / "plan.json").write_bytes(content)
        (output / "plan.sha256").write_text(digest(content) + "\n")
        (output / "receipts").mkdir()
        return result
    except BaseException:
        shutil.rmtree(output)
        raise


def verify(directory: Path) -> dict[str, Any]:
    """Check frozen plan and actor resources before accepting review evidence."""
    path = directory / "plan.json"
    if digest(path.read_bytes()) != (directory / "plan.sha256").read_text().strip():
        raise ValueError("Comparison plan fingerprint mismatch")
    data = read_json(path)
    if data.get("schema") != SCHEMA:
        raise ValueError("Unsupported comparison plan")
    for run in data["runs"]:
        relative = Path(run["actor"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid actor resource path")
        if inventory(directory / relative) != run["files"]:
            raise ValueError(f"Actor resources changed: {run['id']}")
    return data


def record(directory: Path, run_id: str, response: Path, scores: Path, reviewer: str) -> Path:
    """Record an independently supplied semantic rubric with response evidence.

    Scores must contain every criterion once, with integer 0/1/2 and evidence explaining
    the observed behavior. No word matching or agent self-reported score is computed.
    """
    data = verify(directory)
    matches = [run for run in data["runs"] if run["id"] == run_id]
    if len(matches) != 1 or not reviewer.strip():
        raise ValueError("Unknown run or empty independent reviewer identifier")
    run = matches[0]
    case = next(case for case in data["cases"] if case["id"] == run["case"])
    scoring = read_json(scores)
    criteria = {criterion["id"]: criterion for criterion in case["criteria"]}
    if set(scoring) != set(criteria):
        raise ValueError("Review must score exactly the frozen case criteria")
    for key, value in scoring.items():
        if (
            not isinstance(value, dict)
            or set(value) != {"score", "evidence"}
            or type(value["score"]) is not int
            or not 0 <= value["score"] <= criteria[key]["max_score"]
            or not isinstance(value["evidence"], str)
            or not value["evidence"].strip()
        ):
            raise ValueError(f"Invalid semantic review evidence: {key}")
    if response.is_symlink() or not response.is_file() or not response.read_bytes().strip():
        raise ValueError("Response must be a nonempty regular file")
    receipt = directory / "receipts" / f"{run_id}.json"
    result = {
        "run": run_id,
        "case": run["case"],
        "arm": run["arm"],
        "trial": run["trial"],
        "reviewer": reviewer,
        "scores": scoring,
        "response": response.read_bytes().decode("utf-8"),
        "response_sha256": digest(response.read_bytes()),
        "plan_sha256": (directory / "plan.sha256").read_text().strip(),
    }
    with receipt.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return receipt


def report(directory: Path) -> dict[str, Any]:
    """Summarize complete and missing matched observations without superiority claims."""
    data = verify(directory)
    scores: dict[str, list[float]] = {arm: [] for arm in ("baseline", "current", "redesigned")}
    missing = []
    paired: dict[tuple[str, int], dict[str, float]] = {}
    for run in data["runs"]:
        receipt = directory / "receipts" / f"{run['id']}.json"
        if not receipt.exists():
            missing.append(run["id"])
            continue
        result = read_json(receipt)
        if (
            result.get("run") != run["id"]
            or result.get("plan_sha256") != (directory / "plan.sha256").read_text().strip()
            or digest(result["response"].encode()) != result["response_sha256"]
        ):
            raise ValueError(f"Review receipt changed or mismatched: {run['id']}")
        case = next(case for case in data["cases"] if case["id"] == run["case"])
        expected = {criterion["id"] for criterion in case["criteria"]}
        if set(result["scores"]) != expected:
            raise ValueError(f"Receipt criteria mismatch: {run['id']}")
        for criterion in case["criteria"]:
            item = result["scores"][criterion["id"]]
            if (
                not isinstance(item, dict)
                or set(item) != {"score", "evidence"}
                or type(item["score"]) is not int
                or not 0 <= item["score"] <= criterion["max_score"]
                or not isinstance(item["evidence"], str)
                or not item["evidence"].strip()
            ):
                raise ValueError(f"Invalid receipt score/evidence: {run['id']}")
        total = sum(item["score"] for item in result["scores"].values())
        maximum = sum(item["max_score"] for item in case["criteria"])
        score = total / maximum
        scores[run["arm"]].append(score)
        paired.setdefault((run["case"], run["trial"]), {})[run["arm"]] = score
    summary = {
        arm: {
            "observations": len(values),
            "mean": statistics.mean(values) if values else None,
            "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
        }
        for arm, values in scores.items()
    }
    differences = {
        arm: [
            values[arm] - values["baseline"]
            for values in paired.values()
            if "baseline" in values and arm in values
        ]
        for arm in ("current", "redesigned")
    }
    return {
        "settings": data["settings"],
        "arms": summary,
        "missing": missing,
        "paired_differences_from_baseline": differences,
        "limits": "Reviewer-scored constructed reasoning tasks; no production or statistical "
        "superiority claim. Report false blockers, missed failures, complexity, "
        "executed verification and cost separately in the review narrative.",
    }


def main() -> int:
    """Run case listing, comparison planning, integrity verification, recording or report."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    planning = commands.add_parser("plan")
    planning.add_argument("--output", type=Path, required=True)
    planning.add_argument("--current-skill", type=Path, required=True)
    planning.add_argument("--redesigned-skill", type=Path, default=SKILL_ROOT)
    planning.add_argument("--case", action="append", default=[])
    planning.add_argument("--trials", type=int, default=3)
    planning.add_argument("--seed", type=int, default=0)
    planning.add_argument("--model", required=True)
    planning.add_argument("--effort", required=True)
    planning.add_argument("--budget", required=True)
    planning.add_argument("--source-library", type=Path)
    for name in ("verify", "report"):
        command = commands.add_parser(name)
        command.add_argument("directory", type=Path)
    recording = commands.add_parser("record")
    recording.add_argument("directory", type=Path)
    recording.add_argument("--run", required=True)
    recording.add_argument("--response", type=Path, required=True)
    recording.add_argument("--scores", type=Path, required=True)
    recording.add_argument("--reviewer", required=True)
    args = parser.parse_args()
    try:
        if args.command == "list":
            result: Any = [
                {key: case[key] for key in ("id", "title", "chapters")} for case in cases()
            ]
        elif args.command == "plan":
            result = plan(
                args.output,
                args.current_skill,
                args.redesigned_skill,
                selected=args.case,
                trials=args.trials,
                seed=args.seed,
                model=args.model,
                effort=args.effort,
                budget=args.budget,
                source_library=args.source_library,
            )
            result = {
                "runs": len(result["runs"]),
                "directory": str(args.output),
                "limits": result["limits"],
            }
        elif args.command == "record":
            result = {
                "receipt": str(
                    record(args.directory, args.run, args.response, args.scores, args.reviewer)
                )
            }
        elif args.command == "report":
            result = report(args.directory)
        else:
            result = {"runs": len(verify(args.directory)["runs"]), "integrity": "verified"}
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"DDIA evaluation: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
