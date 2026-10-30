"""Adapt Anthropic's paired evaluation files to Codex without custom toolkit dependencies."""

from __future__ import annotations

import hashlib
import json
import math
import runpy
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

from skill_authoring import ROOT, UPSTREAM, native


def read(path: Path) -> bytes:
    """Read a bounded regular file, rejecting aliases and special filesystem entries."""
    if not stat.S_ISREG(path.lstat().st_mode) or path.is_symlink():
        raise ValueError(f"Expected regular file: {path}")
    data = path.read_bytes()
    if len(data) > 32_000_000:
        raise ValueError(f"File exceeds 32 MB: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    """Write controller-owned metadata outside actor tool access."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def verify_upstream() -> None:
    """Verify all vendored files against the pinned upstream Git blob identities."""
    manifest = json.loads(read(ROOT / "UPSTREAM.json"))
    for item in manifest["files"]:
        path = ROOT.parent / item["path"]
        data = read(path)
        digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if digest != item["git_blob_sha"]:
            raise ValueError(f"Pinned upstream file changed: {path}")


def files(path: Path) -> dict[str, bytes]:
    """Snapshot regular files below a non-aliased directory."""
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"Expected directory: {path}")
    result = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink() or not (item.is_dir() or item.is_file()):
            raise ValueError(f"Unsupported filesystem entry: {item}")
        if item.is_file() and "__pycache__" not in item.parts:
            result[item.relative_to(path).as_posix()] = read(item)
    return result


def install_snapshot(
    snapshot: dict[str, bytes], destination: Path, modes: dict[str, int] | None = None
) -> None:
    """Materialize a validated in-memory snapshot without following existing links."""
    for name, content in snapshot.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if modes is not None:
            path.chmod(modes[name])


def runtime_skill(path: Path) -> dict[str, bytes]:
    """Select standard runtime resources, excluding curator tests and grader prompts."""
    snapshot = {"SKILL.md": read(path / "SKILL.md")}
    for directory in ("references", "scripts", "assets"):
        if (path / directory).exists():
            snapshot.update({f"{directory}/{k}": v for k, v in files(path / directory).items()})
    if (path / "agents/openai.yaml").exists():
        snapshot["agents/openai.yaml"] = read(path / "agents/openai.yaml")
    return snapshot


def cases(evals: Path, skill: Path) -> tuple[str, list[dict[str, Any]]]:
    """Validate Anthropic-style cases, including optional local invocation mode.

    Parameters
    ----------
    evals : Path
        Curator-owned evals.json file.
    skill : Path
        Runtime skill root; input file paths follow upstream's skill-root convention.
    """
    data = json.loads(read(evals))
    if not isinstance(data, dict):
        raise ValueError("evals must be a JSON object")
    name = data.get("skill_name")
    if name != skill.name or not isinstance(data.get("evals"), list) or not data["evals"]:
        raise ValueError("evals needs a matching skill_name and a nonempty evals list")
    seen = set()
    prepared = []
    for case in data["evals"]:
        if not isinstance(case, dict):
            raise ValueError("Every case must be an object")
        identifier = case.get("id")
        if type(identifier) is not int or identifier in seen or identifier < 0:
            raise ValueError("Case IDs must be unique nonnegative integers")
        seen.add(identifier)
        for key in ("prompt", "expected_output"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"Case {identifier} needs {key}")
        assertions = case.get("expectations", case.get("assertions", []))
        if "expectations" in case and "assertions" in case and case["assertions"] != assertions:
            raise ValueError("Conflicting expectations and assertions")
        if not isinstance(assertions, list) or any(
            not isinstance(x, str) or not x.strip() for x in assertions
        ):
            raise ValueError("Expectations must be nonempty strings")
        if len(set(assertions)) != len(assertions):
            raise ValueError("Duplicate expectation")
        mode = case.get("invocation", "explicit")
        if mode not in ("explicit", "implicit"):
            raise ValueError("invocation must be explicit or implicit")
        inputs = {}
        if not isinstance(case.get("files", []), list):
            raise ValueError("Case files must be a list")
        for filename in case.get("files", []):
            if not isinstance(filename, str):
                raise ValueError("Input path must be a string")
            relative = Path(filename)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or any(p.startswith(".") for p in relative.parts)
            ):
                raise ValueError(
                    "Input paths must stay under the skill root without hidden configuration"
                )
            source = skill / relative
            if not source.resolve().is_relative_to(skill) or any(
                p.is_symlink() for p in [source, *source.parents] if p != skill.parent
            ):
                raise ValueError("Input alias is not supported")
            inputs[filename] = read(source)
        prepared.append({**case, "expectations": assertions, "invocation": mode, "inputs": inputs})
    return name, prepared


def run(
    evals: Path,
    skill: Path,
    output: Path,
    codex: Path,
    auth: Path,
    model: str,
    effort: str,
    repetitions: int,
    seconds: int,
) -> dict[str, Any]:
    """Execute fresh paired Codex sessions and retain every attempt, including setup failures."""
    verify_upstream()
    if not model.strip() or effort not in ("low", "medium", "high", "xhigh"):
        raise ValueError("Explicit model and supported effort required")
    if repetitions not in range(1, 11) or seconds not in range(1, 3601):
        raise ValueError("repetitions must be 1..10; seconds must be 1..3600")
    if skill.is_symlink():
        raise ValueError("Use a regular skill directory")
    skill = skill.resolve()
    if output.resolve().is_relative_to(skill):
        raise ValueError("Use a regular skill directory and an output outside it")
    name, tasks = cases(evals, skill)
    snapshot = runtime_skill(skill)
    modes = {name: stat.S_IMODE((skill / name).stat().st_mode) for name in snapshot}
    read(auth)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    plan: dict[str, Any] = {
        "version": 1,
        "skill_name": name,
        "model": model,
        "effort": effort,
        "repetitions": repetitions,
        "seconds": seconds,
        "comparison": "runtime skill package",
        "skill_files": {k: hashlib.sha256(v).hexdigest() for k, v in snapshot.items()},
        "skill_modes": modes,
        "case_ids": [task["id"] for task in tasks],
        "runs": [],
    }
    for task in tasks:
        case_root = output / f"eval-{task['id']}"
        metadata = {k: v for k, v in task.items() if k != "inputs"}
        metadata["eval_id"] = task["id"]
        write_json(case_root / "eval_metadata.json", metadata)
        for repeat in range(1, repetitions + 1):
            order = (
                ("with_skill", "without_skill") if repeat % 2 else ("without_skill", "with_skill")
            )
            for arm in order:
                plan["runs"].append(f"eval-{task['id']}/{arm}/run-{repeat}")
    write_json(output / "plan.json", plan)
    for relative in plan["runs"]:
        case_name, arm, _ = relative.split("/")
        task = next(t for t in tasks if case_name == f"eval-{t['id']}")
        root = output / relative
        root.mkdir(parents=True)
        record: dict[str, Any] = {"status": "setup_error", "total_tokens": None}
        credential = root / "client/auth.json"
        try:
            environment = native.configure(root, codex, model, effort)
            install_snapshot(task["inputs"], root / "workspace")
            if arm == "with_skill":
                install_snapshot(snapshot, root / "home/.agents/skills" / name, modes)
            record["isolation"] = native.preflight(root, codex, environment)
            credential.write_bytes(read(auth))
            credential.chmod(0o600)
            prompt = task["prompt"]
            if arm == "with_skill" and task["invocation"] == "explicit":
                prompt = f"Use ${name} for this task.\n\n" + prompt
            prompt += "\n\nSave deliverables under outputs/ and report actual checks and limits."
            write_json(
                root / "eval_metadata.json", {"eval_id": task["id"], "prompt": task["prompt"]}
            )
            result = native.execute(
                [
                    str(codex),
                    "exec",
                    "--strict-config",
                    "--ignore-rules",
                    "--ephemeral",
                    "--skip-git-repo-check",
                    "--json",
                    "--color",
                    "never",
                    "-C",
                    str(root / "workspace"),
                    "-o",
                    str(root / "final.txt"),
                    "-",
                ],
                root / "workspace",
                environment,
                prompt,
                seconds,
            )
            record.update(result)
            record["total_tokens"] = native.tokens(result["stdout"])
            record["status"] = (
                "completed"
                if result["returncode"] == 0
                and not result["timed_out"]
                and not result["output_limited"]
                else "failed"
            )
            (root / "trace.jsonl").write_text(result["stdout"])
            (root / "stderr.txt").write_text(result["stderr"])
            produced = root / "workspace/outputs"
            install_snapshot(files(produced) if produced.exists() else {}, root / "outputs")
            (root / "outputs").mkdir(exist_ok=True)
            if (root / "final.txt").is_file():
                (root / "outputs/response.md").write_bytes(read(root / "final.txt"))
            write_json(
                root / "timing.json",
                {
                    "total_tokens": record["total_tokens"],
                    "total_duration_seconds": result["total_duration_seconds"],
                    "duration_ms": round(result["total_duration_seconds"] * 1000),
                },
            )
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            record["error"] = str(exc)
        finally:
            credential.unlink(missing_ok=True)
            write_json(root / "status.json", record)
    return plan


def report(output: Path) -> dict[str, Any]:
    """Validate complete paired grades before invoking upstream aggregation and static review."""
    verify_upstream()
    plan = json.loads(read(output / "plan.json"))
    identifiers = plan.get("case_ids")
    repetitions = plan.get("repetitions")
    if (
        not isinstance(identifiers, list)
        or not identifiers
        or any(type(i) is not int or i < 0 for i in identifiers)
        or len(set(identifiers)) != len(identifiers)
        or type(repetitions) is not int
        or repetitions not in range(1, 11)
    ):
        raise ValueError("Invalid declared cases or repetitions")
    expected = {
        f"eval-{identifier}/{arm}/run-{repeat}"
        for identifier in identifiers
        for arm in ("with_skill", "without_skill")
        for repeat in range(1, repetitions + 1)
    }
    planned = plan.get("runs")
    if (
        not isinstance(planned, list)
        or any(not isinstance(p, str) for p in planned)
        or len(planned) != len(expected)
        or set(planned) != expected
    ):
        raise ValueError("Plan must contain exactly both arms for every case and repetition")
    discovered = {p.relative_to(output).as_posix() for p in output.glob("eval-*/*/run-*")}
    if discovered != expected or (output / "runs").exists():
        raise ValueError("On-disk runs differ from the declared paired comparison")
    for relative in plan["runs"]:
        run_root = output / relative
        status = json.loads(read(run_root / "status.json"))
        if status.get("status") != "completed":
            raise ValueError(f"Incomplete run retained; cannot claim a comparison: {relative}")
        grade = json.loads(read(run_root / "grading.json"))
        metadata = json.loads(read(output / relative.split("/")[0] / "eval_metadata.json"))
        entries = grade.get("expectations", [])
        if not entries or [e.get("text") for e in entries] != metadata["expectations"]:
            raise ValueError(f"Grade must cover every declared expectation: {relative}")
        if any(
            type(e.get("passed")) is not bool
            or not isinstance(e.get("evidence"), str)
            or not e["evidence"].strip()
            for e in entries
        ):
            raise ValueError(f"Every grade needs a boolean result and evidence: {relative}")
        passed = sum(e["passed"] for e in entries)
        summary = {
            "passed": passed,
            "failed": len(entries) - passed,
            "total": len(entries),
            "pass_rate": passed / len(entries),
        }
        if grade.get("summary") != summary:
            raise ValueError(f"Grade summary disagrees with outcomes: {relative}")
        timing = json.loads(read(run_root / "timing.json"))
        if type(timing.get("total_tokens")) is not int or timing["total_tokens"] < 0:
            raise ValueError(
                "Observed token usage is missing; upstream must not substitute output characters"
            )
        elapsed = timing.get("total_duration_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed <= 0:
            raise ValueError("Positive observed timing is required")
    aggregate = runpy.run_path(str(UPSTREAM / "anthropic/scripts/aggregate_benchmark.py"))
    benchmark: dict[str, Any] = aggregate["generate_benchmark"](
        output, plan["skill_name"], "runtime skill package"
    )
    measured: dict[str, list[dict[str, Any]]] = {}
    for item in benchmark["runs"]:
        relative = f"eval-{item['eval_id']}/{item['configuration']}/run-{item['run_number']}"
        timing = json.loads(read(output / relative / "timing.json"))
        item["result"].update(
            tokens=timing["total_tokens"], time_seconds=timing["total_duration_seconds"]
        )
        measured.setdefault(item["configuration"], []).append(item["result"])
    benchmark["run_summary"] = aggregate["aggregate_results"](measured)
    benchmark["metadata"].update(
        executor_model=plan["model"],
        analyzer_model="not_run",
        runs_per_configuration=plan["repetitions"],
    )
    benchmark["notes"] = [
        "Paired development cases; not independent held-out performance evidence."
    ]
    write_json(output / "benchmark.json", benchmark)
    (output / "benchmark.md").write_text(aggregate["generate_markdown"](benchmark))
    viewer = runpy.run_path(str(UPSTREAM / "anthropic/eval-viewer/generate_review.py"))
    views = []
    for relative in planned:
        run_root = output / relative
        view = viewer["build_run"](output, run_root)
        view["outputs"] = [
            {**viewer["embed_file"](run_root / "outputs" / name), "name": name}
            for name in files(run_root / "outputs")
        ]
        views.append(view)
    html: str = viewer["generate_html"](views, plan["skill_name"], benchmark=benchmark)
    # Escape only embedded JSON, preserving the upstream viewer's actual script tags.
    start = html.index("const EMBEDDED_DATA = ") + len("const EMBEDDED_DATA = ")
    _, length = json.JSONDecoder().raw_decode(html[start:])
    embedded = html[start : start + length].replace("<", "\\u003c")
    (output / "review.html").write_text(html[:start] + embedded + html[start + length :])
    return benchmark


def blind(output: Path, destination: Path) -> None:
    """Prepare A/B output copies and keep the arm mapping outside the reviewer bundle."""
    plan = json.loads(read(output / "plan.json"))
    destination.mkdir(parents=True, exist_ok=False)
    mapping = {}
    for relative in plan["runs"]:
        case, arm, run_id = relative.split("/")
        pair = f"{case}-{run_id}"
        flip = int(hashlib.sha256(pair.encode()).hexdigest(), 16) % 2
        label = (
            ("A" if arm == "with_skill" else "B") if flip else ("B" if arm == "with_skill" else "A")
        )
        install_snapshot(files(output / relative / "outputs"), destination / pair / label)
        metadata = json.loads(read(output / case / "eval_metadata.json"))
        write_json(
            destination / pair / "task.json",
            {"prompt": metadata["prompt"], "assertions": metadata["expectations"]},
        )
        mapping[f"{pair}/{label}"] = relative
    shutil.copyfile(UPSTREAM / "anthropic/agents/comparator.md", destination / "comparator.md")
    write_json(output / "blind-map.json", mapping)
