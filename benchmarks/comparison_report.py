"""Outcome accounting, blind review packets, and sanitized matched reports."""

from __future__ import annotations

import hashlib
import json
import random
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import Any

from benchmarks.comparison import ROLE_ARMS, SUITE, attempt_directory, case_for
from benchmarks.comparison_cases import ROLE_CASES
from benchmarks.files import read_regular
from benchmarks.runtime import fingerprint

REPORT_NOTE = (
    "Fixture validation and a single demonstration do not establish a performance advantage. "
    "Named roles require native dispatch evidence. Pricing and missing telemetry are unavailable."
)


def review_id(result: dict[str, Any]) -> str:
    """Bind a blinded review to this exact submission and product state."""
    return fingerprint(
        {
            key: result[key]
            for key in (
                "run_id",
                "case_fingerprint",
                "submission_sha256",
                "artifact_hashes",
                "grade_evidence_sha256",
            )
        }
    )


def review_flags(case_id: str) -> set[str]:
    """Name the binary judgments required by each public review control."""
    if case_id == "rollback-seeded":
        return {"caught_regression", "false_positive", "safe_correction"}
    if case_id == "rollback-clean":
        return {"false_positive"}
    return set()


def export_reviews(
    root: Path, plan: dict[str, Any], results: list[dict[str, Any]], destination: Path
) -> int:
    """Export individual randomized packets without condition or campaign labels."""
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    count = 0
    for index, data in enumerate(results):
        if data["status"] != "needs_review" or not data.get("submission_sha256"):
            continue
        source = root / attempt_directory(index, plan["entries"][index])
        case = case_for(data["case_id"], plan.get("held_out"))
        label = review_id(data)
        packet = destination / label
        packet.mkdir()
        submission = read_regular(source / "submission.txt")
        (packet / "submission.txt").write_bytes(submission)
        files = data["artifact_hashes"]
        for name in files:
            target = packet / "artifact" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(read_regular(source / "artifact" / name))
        receipt = {
            "review_id": label,
            "prompt": case.prompt,
            "rubric": list(case.rubric),
            "submission_sha256": hashlib.sha256(submission).hexdigest(),
            "artifact_hashes": files,
            "objective_checks": data["grade"]["checks"],
            "required_flags": sorted(review_flags(data["case_id"])),
        }
        if read_regular(source / "initial.diff"):
            (packet / "input.diff").write_bytes(read_regular(source / "initial.diff"))
        (packet / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        count += 1
    return count


def resolve_review(value: Any, *, held_out: bool, flags: set[str] | None = None) -> dict[str, Any]:
    """Require recorded evidence and independent judgments for held-out conclusions."""
    if not isinstance(value, dict) or set(value) - {"scores", "adjudication"}:
        raise ValueError("review receipt requires scores and optional adjudication")
    scores = value.get("scores")
    expected = {"reviewer", "pass", "evidence"} | ({"flags"} if flags else set())
    if not isinstance(scores, list) or len(scores) != (2 if held_out else 1):
        raise ValueError("review must include the required independent scores")
    assessors = set()
    for score in [*scores, *([value["adjudication"]] if "adjudication" in value else [])]:
        if (
            not isinstance(score, dict)
            or set(score) != expected
            or not isinstance(score["reviewer"], str)
            or not score["reviewer"].strip()
            or type(score["pass"]) is not bool
            or not isinstance(score["evidence"], str)
            or not score["evidence"].strip()
            or score["reviewer"].strip() in assessors
        ):
            raise ValueError("invalid or duplicate grader evidence")
        assessors.add(score["reviewer"].strip())
        if flags:
            items = score["flags"]
            if (
                not isinstance(items, dict)
                or set(items) != flags
                or not all(type(item) is bool for item in items.values())
                or score["pass"]
                != (
                    not items["false_positive"]
                    and items.get("caught_regression", True)
                    and items.get("safe_correction", True)
                )
            ):
                raise ValueError("review verdict does not match its structured flags")
    if len({fingerprint([score["pass"], score.get("flags")]) for score in scores}) == 1:
        if "adjudication" in value:
            raise ValueError("unexpected adjudication for agreeing graders")
        return dict(scores[0])
    if "adjudication" not in value:
        raise ValueError("disagreeing graders require independent adjudication")
    return dict(value["adjudication"])


def paired_estimate(
    effects: dict[str, list[float]], clusters: dict[str, str], analysis: dict[str, Any]
) -> dict[str, Any]:
    """Estimate equally weighted task effects and resample independent clusters."""
    per_task = {task: statistics.mean(values) for task, values in effects.items() if values}
    if not per_task:
        return {"effect": None, "cluster_count": 0, "interval": None, "qualifies": False}
    group: dict[str, list[float]] = {}
    for task, effect in per_task.items():
        group.setdefault(clusters[task], []).append(effect)
    interval = None
    if len(group) >= analysis["min_clusters"]:
        rng = random.Random(20261113)
        population = [group[key] for key in sorted(group)]
        if len(set(per_task.values())) == 1:
            # A percentile bootstrap is degenerate when all observed differences match.
            # Retain the estimate but require more informative evidence for a claim.
            interval = None
        else:
            draws = []
            for _ in range(10_000):
                sample = rng.choices(population, k=len(population))
                draws.append(statistics.mean(value for cluster in sample for value in cluster))
            draws.sort()
            tail = analysis["alpha"] / (2 * analysis["claim_count"])
            interval = [draws[int(tail * 10_000)], draws[min(9999, int((1 - tail) * 10_000))]]
    return {
        "effect": statistics.mean(per_task.values()),
        "cluster_count": len(group),
        "interval": interval,
        "qualifies": bool(interval and interval[0] > analysis["minimum_effect"]),
    }


def safe_dispatch(data: dict[str, Any]) -> dict[str, Any]:
    """Project observable dispatch without session identifiers, paths, or raw traces."""
    receipt = data.get("session_dispatch_evidence", {})
    roles = [
        entry["agent_role"]
        for entry in receipt.get("observations", [])
        if entry.get("agent_role") in ROLE_CASES
    ]
    return {
        "status": data.get("dispatch_status", receipt.get("status", "unavailable")),
        "named_roles": sorted(set(roles)),
        "observed_workers": (
            len(receipt.get("observations", [])) if receipt.get("status") == "observed" else None
        ),
    }


def matched_report(
    plan: dict[str, Any],
    results: list[dict[str, Any]],
    reviews: dict[str, Any],
    objective_outcome: Callable[[dict[str, Any]], bool | None],
) -> dict[str, Any]:
    """Account for every scheduled slot and publish only structured evidence."""
    available_reviews = set()
    slots = []
    blocks: dict[tuple[str, str, str, int], dict[str, dict[str, Any]]] = {}
    analysis = plan["held_out"]["analysis"] if plan.get("held_out") else None
    for data in results:
        objective = objective_outcome(data)
        decision = objective
        blind_id = None
        assessment = None
        if data["status"] == "needs_review":
            decision = None
            blind_id = review_id(data)
            available_reviews.add(blind_id)
            if blind_id in reviews:
                assessment = resolve_review(
                    reviews[blind_id],
                    held_out=analysis is not None,
                    flags=review_flags(data["case_id"]),
                )
                decision = assessment["pass"]
        elif data["status"] in {"failed", "timed_out"}:
            decision = False
        usage = data.get("reported_root_usage") or {}
        aggregate = data.get("aggregate_tree_tokens")
        slot: dict[str, Any] = {
            key: data.get(key)
            for key in (
                "case_id",
                "case_fingerprint",
                "comparison",
                "role",
                "cluster",
                "arm",
                "attempt",
                "status",
                "prompt_fingerprint",
                "product_hashes",
                "treatment_hashes",
                "artifact_hashes",
                "submission_sha256",
                "grade_evidence_sha256",
                "wall_elapsed_seconds",
            )
        }
        slot["root_usage"] = {
            key: usage[key]
            for key in (
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            )
            if type(usage.get(key)) is int and usage[key] >= 0
        } or None
        slot.update(
            {
                "tree_tokens": aggregate if type(aggregate) is int and aggregate >= 0 else None,
                "cost": None,
                "objective_pass": objective,
                "task_success": decision,
                "review_id": blind_id,
                "review_flags": assessment.get("flags") if assessment else None,
                "dispatch": safe_dispatch(data),
                "skill_read_calls_observed": [
                    name
                    for name in data.get("skill_read_calls_observed", [])
                    if any(path.endswith(f"/{name}/SKILL.md") for path in data["treatment_hashes"])
                ],
                "review_scores": [score["pass"] for score in reviews[blind_id]["scores"]]
                if blind_id in reviews
                else None,
                "review_adjudication": (
                    reviews[blind_id].get("adjudication", {}).get("pass")
                    if blind_id in reviews
                    else None
                ),
                "review_evidence_fingerprint": (
                    fingerprint(reviews[blind_id]) if blind_id in reviews else None
                ),
            }
        )
        key = (data["comparison"], data["role"] or "", data["case_id"], data["attempt"])
        blocks.setdefault(key, {})[data["arm"]] = slot
        slots.append(slot)
    if set(reviews) - available_reviews:
        raise ValueError("review file contains unknown or stale submission identities")

    comparisons: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for (track, role, case_id, _), arms in blocks.items():
        if track == "role":
            pairings = [(arm, "named-worker") for arm in ROLE_ARMS[:-1]]
        else:
            pairings = [
                (arm, "default-toolkit") for arm in ("stock", "single-agent") if arm in arms
            ]
        for control, treatment in pairings:
            key = (track, role, control, treatment)
            pair = comparisons.setdefault(
                key,
                {
                    "track": track,
                    "role": role or None,
                    "control": control,
                    "treatment": treatment,
                    "wins": 0,
                    "ties": 0,
                    "losses": 0,
                    "incomplete": 0,
                    "effects": {},
                    "worst_case": {},
                    "clusters": {},
                    "control_successes": 0,
                    "treatment_successes": 0,
                },
            )
            a, b = arms[control], arms[treatment]
            pair["clusters"][case_id] = a["cluster"]
            pair.setdefault("control_times", []).extend(
                [a["wall_elapsed_seconds"]] if a["wall_elapsed_seconds"] is not None else []
            )
            pair.setdefault("treatment_times", []).extend(
                [b["wall_elapsed_seconds"]] if b["wall_elapsed_seconds"] is not None else []
            )
            pair["control_tree_usage"] = pair.get("control_tree_usage", 0) + int(
                a["tree_tokens"] is not None
            )
            pair["treatment_tree_usage"] = pair.get("treatment_tree_usage", 0) + int(
                b["tree_tokens"] is not None
            )
            first, second = a["task_success"], b["task_success"]
            pair["control_successes"] += int(first is True)
            pair["treatment_successes"] += int(second is True)
            if first is None or second is None:
                pair["incomplete"] += 1
                pair["worst_case"].setdefault(case_id, []).append(
                    int(second is True) - int(first is not False)
                )
                continue
            difference = int(second) - int(first)
            pair[{1: "wins", 0: "ties", -1: "losses"}[difference]] += 1
            pair["effects"].setdefault(case_id, []).append(difference)
            pair["worst_case"].setdefault(case_id, []).append(difference)
    for pair in comparisons.values():
        effects, worst, clusters = (
            pair.pop(field) for field in ("effects", "worst_case", "clusters")
        )
        pair["distinct_tasks"] = len(clusters)
        pair["scheduled_pairs"] = sum(pair[key] for key in ("wins", "ties", "losses", "incomplete"))
        for condition in ("control", "treatment"):
            times = pair.pop(f"{condition}_times")
            pair[f"{condition}_median_seconds"] = statistics.median(times) if times else None
        pair["estimate"] = paired_estimate(effects, clusters, analysis) if analysis else None
        pair["missing_outcomes_bound"] = (
            paired_estimate(worst, clusters, analysis) if analysis else None
        )
        estimate = pair["estimate"] or {}
        bound = pair["missing_outcomes_bound"] or {}
        pair["meets_public_improvement_rule"] = bool(
            estimate.get("qualifies") and bound.get("qualifies")
        )
    coverage = {}
    for role in ROLE_CASES:
        matching = [row for row in slots if row["role"] == role and row["arm"] == "named-worker"]
        coverage[role] = {
            "scheduled": len(matching),
            "observed": sum(row["dispatch"]["status"] == "observed" for row in matching),
            "scored": sum(row["task_success"] is not None for row in matching),
        }
    return {
        "suite": SUITE,
        "plan_fingerprint": fingerprint(plan),
        "toolkit_fingerprint": plan["toolkit_package_fingerprint"],
        "harness_fingerprint": plan["harness_fingerprint"],
        "host": plan["host"],
        "toolkit_commit": plan.get("toolkit_commit"),
        "model": plan["model"],
        "effort": plan["effort"],
        "wall_seconds": plan["wall_seconds"],
        "budget_units": plan["budget_units"],
        "source_profile": plan["resource_profile"],
        "stage": "held-out" if analysis else "exploratory",
        "analysis": analysis,
        "comparisons": list(comparisons.values()),
        "role_coverage": coverage,
        "slots": slots,
        "review_findings": {
            arm: {
                key: sum(
                    slot["review_flags"].get(key, False)
                    for slot in slots
                    if slot["arm"] == arm and slot["review_flags"] is not None
                )
                for key in ("caught_regression", "false_positive", "safe_correction")
            }
            for arm in sorted({slot["arm"] for slot in slots if slot["review_flags"] is not None})
        },
        "note": REPORT_NOTE,
    }


def markdown_report(report: dict[str, Any]) -> str:
    """Render a slim standalone report beside its structured evidence."""
    header = [
        "# Agent Toolkit paired benchmark",
        "",
        f"{report['stage'].capitalize()} campaign. Model {report['model']} "
        f"at {report['effort']} effort. {report['host']['codex_version']} on "
        f"{report['host']['system']} {report['host']['machine']}. "
        f"Wall deadline {report['wall_seconds']} seconds per session.",
        "",
        report["note"],
        "",
        "| Comparison | Control | Treatment | Tasks | Scheduled pairs | Wins | Ties | "
        "Losses | Incomplete | Lift | Interval |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for pair in report["comparisons"]:
        label = pair["role"] or pair["track"]
        estimate = pair["estimate"] or {}
        effect, interval = estimate.get("effect"), estimate.get("interval")
        lift = f"{effect:+.1%}" if effect is not None else "—"
        bounds = f"{interval[0]:+.1%} to {interval[1]:+.1%}" if interval else "—"
        header.append(
            f"| {label} | {pair['control']} | {pair['treatment']} | {pair['distinct_tasks']} | "
            f"{pair['scheduled_pairs']} | {pair['wins']} | {pair['ties']} | "
            f"{pair['losses']} | {pair['incomplete']} | {lift} | {bounds} |"
        )
    if report["review_findings"]:
        header += [
            "",
            "## SQLite review findings",
            "",
            "| Arm | Regressions caught | False positives | Safe corrections |",
            "| --- | ---: | ---: | ---: |",
        ]
        for arm, findings in report["review_findings"].items():
            header.append(
                f"| {arm} | {findings['caught_regression']} | "
                f"{findings['false_positive']} | {findings['safe_correction']} |"
            )
    header += [
        "",
        "## Named role coverage",
        "",
        "| Role | Planned | Observed | Scored |",
        "| --- | ---: | ---: | ---: |",
    ]
    for role, counts in report["role_coverage"].items():
        header.append(
            f"| {role} | {counts['scheduled']} | {counts['observed']} | {counts['scored']} |"
        )
    header += [
        "",
        "## Scheduled attempts",
        "",
        "| Task | Role | Arm | Repeat | Status | Task success | Seconds | "
        "Root tokens | Tree tokens |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for slot in report["slots"]:
        root = slot["root_usage"] or {}
        observed = (
            f"{root['input_tokens'] + root['output_tokens']:,}"
            if {"input_tokens", "output_tokens"} <= root.keys()
            else "—"
        )
        elapsed = slot["wall_elapsed_seconds"]
        seconds = f"{elapsed:.2f}" if elapsed is not None else "—"
        tree = slot["tree_tokens"] if slot["tree_tokens"] is not None else "—"
        success = slot["task_success"] if slot["task_success"] is not None else "—"
        header.append(
            f"| {slot['case_id']} | {slot['role'] or '—'} | {slot['arm']} | "
            f"{slot['attempt']} | {slot['status']} | {success} | {seconds} | {observed} | {tree} |"
        )
    return "\n".join(header) + "\n"
