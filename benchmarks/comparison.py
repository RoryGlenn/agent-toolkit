"""Versioned matched campaigns using the existing benchmark runner."""

from __future__ import annotations

import json
import os
import platform
import random
import re
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import install
import project_bootstrap
from benchmarks.cases import REPOSITORY
from benchmarks.comparison_cases import (
    DEMO_CASES,
    EXTRA_CASES,
    FULL_CASES,
    RECORD_CASES,
    ROLE_CASES,
    ComparisonCase,
    comparison_case,
)
from benchmarks.files import copy_snapshot, hashes, read_regular, snapshot
from benchmarks.process import bounded_process, sanitized_environment
from benchmarks.runtime import (
    NativeExecutor,
    config_text,
    digest,
    fingerprint,
    git_runtime,
    harness_fingerprint,
    stage_runtime,
    toolkit_manifest,
)

SUITE = "matched-toolkit-v2"
HEADLINE_ARMS = ("stock", "default-toolkit")
ROLE_ARMS = ("single-agent", "generic-worker", "named-worker")
GENERIC_ROLE = "benchmark_generic_worker"
GENERIC_ROLE_FILE = ".codex/agents/benchmark-generic-worker.toml"
GENERIC_GUIDANCE = (
    f'name = "{GENERIC_ROLE}"\n'
    'description = "Generic coding worker for the assigned benchmark task."\n'
    'developer_instructions = """Complete the assigned task using the available tools. '
    "Stay within the requested scope. Return the result and the checks you performed. "
    'Complete the work in this session."""\n'
).encode()
MANAGED = frozenset({".git", ".agents", ".codex", ".agent-toolkit", "AGENTS.md"})
HANDOFF = (
    "First call spawn_agent with agent_type={role} and fork_context=false, passing the exact "
    "user message as the message value. Wait for that one worker to finish. "
    "Only the worker may run commands, edit files or decide the answer. "
    "Do not send follow-up instructions or use any other tools."
)
SOLE_WRITER = (
    "You are the sole writer authorized to implement this task in the current workspace.\n\n"
)


def installed_files(selection: tuple[str, ...]) -> dict[str, bytes]:
    """Resolve bootstrap's actual portable roles and selected dependency closure."""
    skills = project_bootstrap.resolve_skills(list(selection), install.inventory(REPOSITORY))
    collected = project_bootstrap.collect_files(
        REPOSITORY, skills, ["codex"], install.AGENTS, install.IGNORED
    )
    return {path: state.content for path, state in collected.items()}


def treatment_files(arm: str, role: str | None) -> dict[str, bytes]:
    """Declare exact managed bytes, excluding bootstrap's source-provenance receipt."""
    if arm == "default-toolkit":
        selection = project_bootstrap.DEFAULT_SKILLS
        skills = project_bootstrap.resolve_skills(list(selection), install.inventory(REPOSITORY))
        return {
            **installed_files(selection),
            "AGENTS.md": project_bootstrap.instruction_block(skills) + b"\n",
        }
    if arm == "named-worker" and role is not None and role in ROLE_CASES:
        file_name = role.replace("_", "-") + ".toml"
        files = installed_files((ROLE_CASES[role][0],))
        return {
            path: content
            for path, content in files.items()
            if (path.startswith(".agents/") and "evals" not in Path(path).parts)
            or path == f".codex/agents/{file_name}"
        }
    if arm == "generic-worker":
        return {GENERIC_ROLE_FILE: GENERIC_GUIDANCE}
    return {}


def host_identity(codex: Path) -> dict[str, str]:
    """Bind actual binaries and OS when creating or executing a matched campaign."""
    version = bounded_process(
        [str(codex), "--version"],
        REPOSITORY,
        sanitized_environment(Path("/var/empty"), Path("/tmp")),
        timeout=10,
    )
    if version.returncode or not re.fullmatch(r"codex-cli [A-Za-z0-9.+-]+", version.stdout.strip()):
        raise ValueError("could not establish the Codex CLI version")
    git, _, git_version = git_runtime()
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "codex_version": version.stdout.strip(),
        "codex_sha256": digest(codex),
        "python_version": platform.python_version(),
        "python_sha256": digest(Path(sys.executable).resolve()),
        "git_version": git_version,
        "git_sha256": digest(git),
    }


def require_role_protocol(codex: Path, model: str) -> None:
    """Check bundled direct-tool V1 compatibility before controlled worker runs."""
    catalog = bounded_process(
        [str(codex), "debug", "models", "--bundled"],
        REPOSITORY,
        sanitized_environment(Path("/var/empty"), Path("/tmp")),
        timeout=15,
    )
    if catalog.returncode:
        raise ValueError("could not read the Codex model catalog to qualify the worker protocol")
    value = json.loads(catalog.stdout)
    rows = value.get("models", []) if isinstance(value, dict) else value
    if not isinstance(rows, list) or not any(
        isinstance(row, dict)
        and row.get("slug") == model
        and row.get("multi_agent_version") in {None, "v1"}
        and row.get("tool_mode") not in {"code_mode_only"}
        for row in rows
    ):
        raise ValueError("controlled worker runs require direct-tool Codex V1 support")


def read_held_out(manifest: Path) -> dict[str, Any]:
    """Read curator-owned held-out tasks without staging reference answers for actors."""
    data: dict[str, Any] = json.loads(read_regular(manifest.resolve()))
    validate_held_out(data)
    for case_id, case in data["cases"].items():
        case_for(case_id, data)
        for outcome, control in case["controls"].items():
            path = manifest.resolve().parent / "controls" / case_id / f"{outcome}.json"
            evidence = read_regular(path)
            if fingerprint(json.loads(evidence)) != control["evidence_sha256"]:
                raise ValueError(f"held-out control receipt changed for {case_id}/{outcome}")
            receipt = json.loads(evidence)
            if (
                not isinstance(receipt, dict)
                or receipt.get("case_id") != case_id
                or receipt.get("case_fingerprint") != held_out_case_fingerprint(case)
                or not isinstance(receipt.get("scores"), list)
                or len(receipt["scores"]) != 2
            ):
                raise ValueError(f"held-out control receipt is incomplete for {case_id}/{outcome}")
            reviewers = set()
            for score in receipt["scores"]:
                if (
                    not isinstance(score, dict)
                    or not isinstance(score.get("reviewer"), str)
                    or not score["reviewer"].strip()
                    or not isinstance(score.get("evidence"), str)
                    or not score["evidence"].strip()
                    or score.get("pass") is not control["pass"]
                    or score["reviewer"].strip() in reviewers
                ):
                    raise ValueError(f"held-out control review disagrees for {case_id}/{outcome}")
                reviewers.add(score["reviewer"].strip())
            control["receipt"] = receipt
    return data


def held_out_case_fingerprint(case: dict[str, Any]) -> str:
    """Bind curator control receipts to the rubric and inputs they assessed."""
    return fingerprint({key: value for key, value in case.items() if key != "controls"})


def validate_held_out(data: dict[str, Any]) -> None:
    """Require a predeclared study rule for new cases, including in saved plans."""
    if (
        not isinstance(data, dict)
        or set(data) != {"cases", "analysis"}
        or not isinstance(data["cases"], dict)
    ):
        raise ValueError("held-out manifest requires cases and analysis")
    analysis = data["analysis"]
    if (
        not isinstance(analysis, dict)
        or set(analysis) != {"minimum_effect", "min_clusters", "alpha", "claim_count"}
        or type(analysis["min_clusters"]) is not int
        or analysis["min_clusters"] < 10
        or type(analysis["claim_count"]) is not int
        or not 1 <= analysis["claim_count"] <= 20
        or type(analysis["minimum_effect"]) not in {float, int}
        or not 0 <= analysis["minimum_effect"] < 1
        or analysis["alpha"] != 0.05
    ):
        raise ValueError("invalid held-out analysis rule")
    if not data["cases"]:
        raise ValueError("held-out cases are empty")


def case_for(case_id: str, held_out: dict[str, Any] | None) -> ComparisonCase:
    """Decode a frozen study fixture or load the public calibration template."""
    if held_out is None:
        return comparison_case(case_id)
    if case_id in RECORD_CASES | EXTRA_CASES or not re.fullmatch(r"[a-z][a-z0-9-]{0,50}", case_id):
        raise ValueError("held-out case must have a new, safe identifier")
    case = held_out["cases"][case_id]
    if (
        not isinstance(case, dict)
        or set(case) != {"prompt", "files", "rubric", "cluster", "read_only", "diff", "controls"}
        or not all(
            isinstance(case[key], str) and case[key].strip() for key in ("prompt", "cluster")
        )
        or not isinstance(case["files"], dict)
        or not case["files"]
        or not isinstance(case["rubric"], list)
        or not case["rubric"]
        or not all(isinstance(row, str) and row.strip() for row in case["rubric"])
        or type(case["read_only"]) is not bool
    ):
        raise ValueError("held-out case requires a prompt, files, rubric, cluster and read_only")
    files = {}
    for name, contents in case["files"].items():
        path = Path(name)
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", name)
            or any(part in MANAGED or part in {"..", "."} for part in name.split("/"))
            or not isinstance(contents, str)
            or path.name.startswith(".isolation-")
        ):
            raise ValueError("invalid held-out product path or content")
        files[name] = contents.encode()
    diff = case["diff"]
    if not isinstance(diff, dict) or not set(diff) <= set(files):
        raise ValueError("held-out diff must update paths from the base fixture")
    if not all(isinstance(contents, str) for contents in diff.values()):
        raise ValueError("held-out diff contents must be text")
    controls = case["controls"]
    if (
        not isinstance(controls, dict)
        or set(controls) != {"reference", "wrong"}
        or any(
            not isinstance(control, dict)
            or not {"evidence_sha256", "pass"} <= control.keys()
            or set(control) - {"evidence_sha256", "pass", "receipt"}
            or not isinstance(control["evidence_sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", control["evidence_sha256"])
            or control["pass"] is not (label == "reference")
            for label, control in controls.items()
        )
        or controls["reference"]["evidence_sha256"] == controls["wrong"]["evidence_sha256"]
    ):
        raise ValueError("held-out cases require distinct review evidence for both controls")
    changed = {**files, **{name: contents.encode() for name, contents in diff.items()}}
    return ComparisonCase(
        case_id,
        "held-out",
        case["prompt"],
        changed,
        files,
        tuple(case["rubric"]),
        case["read_only"],
    )


def scheduled_case(case_id: str, held_out: dict[str, Any] | None, track: str) -> ComparisonCase:
    """Give all arms of a write-role task the same explicit ownership."""
    case = case_for(case_id, held_out)
    if track == "role" and not case.read_only:
        return replace(case, prompt=SOLE_WRITER + case.prompt)
    return case


def comparison_plan(
    track: str,
    cases: list[str],
    role: str | None,
    model: str,
    effort: str,
    seconds: int,
    attempts: int,
    budget_units: int | None,
    include_single: bool,
    host: dict[str, str],
    *,
    pilot: bool = False,
    held_out: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze one matched run with deterministic arm order and one prompt per case."""
    if (
        not 1 <= seconds <= 7200
        or not 1 <= attempts <= 4
        or not model.strip()
        or not effort.strip()
    ):
        raise ValueError("require model, effort, 1..7200 seconds and 1..4 attempts")
    if not all(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}", name) for name in (model, effort)
    ):
        raise ValueError("invalid model or effort identifier")
    if budget_units is not None and budget_units < 2:
        raise ValueError("budget requires at least two units")
    if track == "role" and role not in ROLE_CASES:
        raise ValueError("role campaigns require a supported --role")
    if track != "role" and role is not None:
        raise ValueError("--role requires the role comparison")
    if include_single and track != "toolkit":
        raise ValueError("--include-single-agent applies to toolkit comparisons")
    if track not in {"demo", "toolkit", "role"}:
        raise ValueError("unknown comparison track")
    if track == "demo" and cases and not set(cases) <= set(DEMO_CASES):
        raise ValueError("demo cases must be a SQLite review diff")
    if (
        track == "role"
        and role is not None
        and cases
        and not set(cases) <= set(ROLE_CASES[role][1])
    ):
        raise ValueError("selected cases are outside this role's declared scope")
    if len(cases) != len(set(cases)):
        raise ValueError("duplicate comparison case")
    if pilot and (track != "toolkit" or cases or role or include_single or held_out):
        raise ValueError("pilot uses its fixed toolkit and role schedule")
    if held_out is not None:
        validate_held_out(held_out)
        for case in held_out["cases"].values():
            for label, control in case["controls"].items():
                if (
                    not isinstance(control.get("receipt"), dict)
                    or fingerprint(control["receipt"]) != control["evidence_sha256"]
                    or control["receipt"].get("case_fingerprint") != held_out_case_fingerprint(case)
                    or control["pass"] is not (label == "reference")
                ):
                    raise ValueError("held-out plan is missing its verified control receipts")
    if held_out and (cases or track == "demo" or pilot or include_single):
        raise ValueError("held-out inputs form their own toolkit or role campaign")
    if held_out and track == "role" and held_out["analysis"]["claim_count"] < 2:
        raise ValueError("a role campaign compares two baselines and requires claim_count >= 2")
    if pilot and attempts != 2:
        raise ValueError("calibration pilot requires two attempts per condition")

    arms = list(ROLE_ARMS if track == "role" else HEADLINE_ARMS)
    if include_single:
        arms.append("single-agent")
    selected = cases or (
        list(DEMO_CASES if track == "demo" else ROLE_CASES[role][1] if role else FULL_CASES)
    )
    schedule: list[tuple[str, str | None, str, list[str]]] = [
        (track, role, case_id, arms) for case_id in selected
    ]
    if held_out:
        schedule = [(track, role, case_id, arms) for case_id in sorted(held_out["cases"])]
    if pilot:
        for pilot_role in ("adversarial_reviewer_agent", "ddia_agent"):
            schedule.extend(
                ("role", pilot_role, case_id, list(ROLE_ARMS))
                for case_id in ROLE_CASES[pilot_role][1]
            )
    entries = []
    rng = random.Random(20261113)
    treatments: dict[tuple[str, str | None], dict[str, str]] = {}
    for lane, specialist, case_id, choices in schedule:
        case = scheduled_case(case_id, held_out, lane)
        cluster = held_out["cases"][case_id]["cluster"] if held_out else case_id
        for arm in choices:
            key = (arm, specialist)
            if key not in treatments:
                treatments[key] = hashes(treatment_files(arm, specialist))
        for attempt in range(1, attempts + 1):
            order = rng.sample(choices, len(choices))
            for arm in order:
                entries.append(
                    {
                        **case.identity(),
                        "phase": 1,
                        "comparison": lane,
                        "role": specialist,
                        "arm": arm,
                        "attempt": attempt,
                        "planned_arms": choices,
                        "cluster": cluster,
                        "treatment_hashes": treatments[arm, specialist],
                    }
                )
    selection = {
        "track": track,
        "cases": cases,
        "role": role,
        "include_single": include_single,
        "pilot": pilot,
    }
    revision = bounded_process(
        [str(git_runtime()[0]), "rev-parse", "HEAD"],
        REPOSITORY,
        sanitized_environment(Path("/var/empty"), Path("/tmp")),
        timeout=5,
    )
    toolkit_commit = revision.stdout.strip() if revision.returncode == 0 else None
    return {
        "version": 2,
        "suite": SUITE,
        "plan_id": str(uuid.uuid4()),
        "entries": entries,
        "selection": selection,
        "held_out": held_out,
        "host": host,
        "toolkit_commit": toolkit_commit,
        "model": model,
        "effort": effort,
        "model_mode": "controlled",
        "wall_seconds": seconds,
        "attempt_cap": attempts,
        "budget_units": budget_units,
        "source_manifest": None,
        "source_fingerprint": fingerprint([]),
        "toolkit_package_fingerprint": (fingerprint(toolkit_manifest())),
        "harness_fingerprint": harness_fingerprint(comparison=True),
        "resource_profile": "packaged-guidance",
        "parent_result": None,
        "parent_artifact_fingerprint": None,
        "sequel_fingerprint": None,
        "randomization_seed": 20261113,
    }


def verify_comparison_plan(plan: dict[str, Any]) -> None:
    """Reconstruct the frozen schedule from source and the declared input selection."""
    selection = plan["selection"]
    current = comparison_plan(
        selection["track"],
        selection["cases"],
        selection["role"],
        plan["model"],
        plan["effort"],
        plan["wall_seconds"],
        plan["attempt_cap"],
        plan["budget_units"],
        selection["include_single"],
        plan["host"],
        pilot=selection["pilot"],
        held_out=plan.get("held_out"),
    )
    current["plan_id"] = plan["plan_id"]
    if current != plan:
        raise ValueError("matched schedule, case, treatment or harness changed since planning")


def attempt_directory(index: int, entry: dict[str, Any]) -> str:
    """Name one immutable scheduled position in a campaign."""
    return f"{index:03d}-{entry['case_id']}-{entry['arm']}-{entry['attempt']}"


def verify_product_permissions(executor: NativeExecutor, readonly: list[Path]) -> dict[str, bool]:
    """Require existing fixture/metadata writes to obey their declared boundary."""
    if not readonly:
        return {}
    source = """import errno, json, os, sys
result = {}
for path in sys.argv[1:]:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_APPEND)
    except OSError as error:
        result[path] = error.errno in (errno.EPERM, errno.EACCES, errno.EROFS)
    else:
        os.close(fd)
        result[path] = False
print(json.dumps(result))
"""
    check = executor.execute(
        [
            str(Path(sys.executable).resolve()),
            "-I",
            "-B",
            "-c",
            source,
            *(str(executor.workspace / path) for path in readonly),
        ],
        executor.workspace,
    )
    if check.returncode:
        raise ValueError("could not verify protected project paths")
    data: dict[str, bool] = json.loads(check.stdout)
    if len(data) != len(readonly) or not all(value is True for value in data.values()):
        raise ValueError("native permission profile allows writes to protected project files")
    return {path.as_posix(): True for path in readonly}


def git_command(workspace: Path, home: Path, temporary: Path, *args: str) -> bytes:
    """Prepare local Git fixture data without reading host config or running hooks."""
    git, _, _ = git_runtime()
    environment = sanitized_environment(home, temporary)
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
    )
    result = bounded_process(
        [
            str(git),
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=Benchmark",
            "-c",
            "user.email=benchmark@example.invalid",
            *args,
        ],
        workspace,
        environment,
        timeout=10,
    )
    if result.returncode or result.output_limited:
        raise ValueError(f"Git fixture operation failed: {args[0]}: {result.stderr}")
    return result.stdout.encode()


def catalog_skill_paths(body: str) -> set[str]:
    """Read exact host locators and resolve Codex's scoped catalog aliases."""
    locators: set[str] = set()
    aliases: dict[str, str] = {}
    section = ""
    for line in body.splitlines():
        if line.startswith("#"):
            section = line.strip()
        if section == "### Skill roots":
            match = re.fullmatch(r"- `(h\d+)` = `(/[^`]+)`", line)
            if match:
                alias, root = match.groups()
                if alias in aliases and aliases[alias] != root:
                    raise ValueError("conflicting skill catalog aliases")
                aliases[alias] = root
        if section == "### Available skills" and line.startswith("- "):
            match = re.search(r"\((?:file|path): ([^)\n]+/SKILL\.md)\)$", line)
            if match:
                path = match[1]
                root, _, rest = path.partition("/")
                if root in aliases:
                    path = str(Path(aliases[root]) / rest)
                locators.add(path)
    return locators


def stage_demo_pair(destination: Path, case_id: str) -> None:
    """Prepare the two public review workspaces without starting a model."""
    if case_id not in DEMO_CASES:
        raise ValueError("demo fixture must be rollback-seeded or rollback-clean")
    destination = destination.resolve()
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    plan = comparison_plan("demo", [case_id], None, "unused", "medium", 180, 1, None, False, {})
    diffs = []
    for entry in plan["entries"]:
        attempt = destination / entry["arm"]
        stage_match(plan, entry, attempt)
        diffs.append(read_regular(attempt / "initial.diff"))
    if diffs[0] != diffs[1]:
        raise ValueError("the two demo diffs differ")


def stage_match(plan: dict[str, Any], entry: dict[str, Any], root: Path) -> dict[str, Any]:
    """Stage exact product and toolkit bytes without exposing control material."""
    case = scheduled_case(entry["case_id"], plan.get("held_out"), entry["comparison"])
    workspace, home, client, temporary = (
        root / name for name in ("workspace", "actor-home", "client-home", "private-tmp")
    )
    copy_snapshot(case.original, workspace)
    for path in (home, client, temporary):
        path.mkdir()
    git = stage_runtime(home)
    git_command(workspace, home, temporary, "init", "--quiet", "--template=")
    git_command(workspace, home, temporary, "add", "--", *case.original)
    git_command(workspace, home, temporary, "commit", "--quiet", "-m", "Start benchmark fixture")
    for name, data in case.files.items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    expected = treatment_files(entry["arm"], entry["role"])
    git_command(workspace, home, temporary, "config", "core.filemode", "false")
    if entry["arm"] == "default-toolkit":
        project_bootstrap.bootstrap(
            REPOSITORY,
            workspace,
            install.inventory(REPOSITORY),
            install.AGENTS,
            install.IGNORED,
            target="codex",
        )
    else:
        for name, data in expected.items():
            file = workspace / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
    actual = {name: digest(workspace / name) for name in expected}
    if actual != entry["treatment_hashes"]:
        raise ValueError("staged treatment differs from the plan")
    if product_hashes(workspace, entry) != entry["product_hashes"]:
        raise ValueError("staged product differs from the plan")
    diff = git_command(workspace, home, temporary, "diff", "--no-ext-diff", "--no-textconv")
    (root / "initial.diff").write_bytes(diff)
    arm = entry["arm"]
    role = entry["role"] if arm == "named-worker" else GENERIC_ROLE
    readonly = [workspace / name for name in sorted(MANAGED) if (workspace / name).exists()]
    configuration = config_text(
        workspace,
        home,
        client,
        temporary,
        plan["model"],
        plan["effort"],
        plan["budget_units"],
        project_instructions=True,
        agents_enabled=arm != "single-agent",
        max_children=1 if arm in ROLE_ARMS else 3,
        writable=not case.read_only,
        readonly=readonly,
        instructions=HANDOFF.format(role=role) if arm in ROLE_ARMS[1:] else "",
    )
    with (client / "config.toml").open("x") as out:
        out.write(configuration)
        os.fchmod(out.fileno(), 0o600)
    (root / "prompt.txt").write_text(case.prompt)
    return {
        "git_runtime": git,
        "config_fingerprint": fingerprint(configuration),
        "git_diff_sha256": digest(root / "initial.diff"),
        "toolkit_files": actual,
        "role_dispatch_observed": [],
        "source_access_observed": [],
    }


def product_snapshot(workspace: Path, entry: dict[str, Any]) -> dict[str, bytes]:
    """Read product artifacts without actor config or the controller's Git fixture."""
    return snapshot(
        workspace, required=tuple(entry["product_hashes"]), excluded_root_entries=MANAGED
    )


def product_hashes(workspace: Path, entry: dict[str, Any]) -> dict[str, str]:
    """Identify the exact matched product snapshot."""
    return hashes(product_snapshot(workspace, entry))


def verify_treatment(workspace: Path, entry: dict[str, Any]) -> None:
    """Reject changes to staged guidance or new reserved configuration after a run."""
    expected = entry["treatment_hashes"]
    actual = hashes({name: read_regular(workspace / name) for name in expected})
    if actual != expected:
        raise ValueError("staged comparison guidance changed")
    for managed in (".agents", ".codex", "AGENTS.md", ".agent-toolkit"):
        path = workspace / managed
        if managed == ".agent-toolkit" and entry["arm"] == "default-toolkit":
            if path.is_symlink() or not path.is_dir():
                raise ValueError("bootstrap receipt boundary changed")
            continue
        allowed = {name for name in expected if name == managed or name.startswith(managed + "/")}
        if path.is_symlink() or (path.exists() and not allowed):
            raise ValueError("actor added or aliased reserved configuration")
        if path.is_dir():
            found = {
                item.relative_to(workspace).as_posix()
                for item in path.rglob("*")
                if item.is_file() or item.is_symlink()
            }
            if found != allowed:
                raise ValueError("staged comparison guidance file list changed")


def worker_output(
    entry: dict[str, Any],
    plan: dict[str, Any],
    observed: dict[str, Any],
) -> tuple[str | None, str]:
    """Accept direct worker evidence only with a matched brief and own turn settings."""
    sessions = observed.get("session_dispatch_evidence", {})
    workers = sessions.get("observations", [])
    if sessions.get("status") != "observed" or len(workers) != 1:
        return None, "worker_count_or_native_metadata_unverified"
    worker = workers[0]
    role = entry["role"]
    label = worker.get("agent_role")
    if worker.get("parent_thread_id") != sessions.get("root_thread_id") or (
        label != (role if entry["arm"] == "named-worker" else GENERIC_ROLE)
    ):
        return None, "worker_role_unverified"
    if (worker.get("model"), worker.get("effort")) != (plan["model"], plan["effort"]):
        return None, "worker_settings_unverified"
    inputs = worker.get("worker_inputs", [])
    if len(inputs) != 1 or fingerprint(inputs[0]) != entry["prompt_fingerprint"]:
        return None, "worker_brief_unverified"
    answer = worker.get("worker_output")
    if (
        worker.get("worker_completed_turns") != 1
        or not isinstance(answer, str)
        or not answer.strip()
    ):
        return None, "worker_output_unavailable"
    return answer, "observed"


def handoff_matches(
    entry: dict[str, Any], trace: dict[str, Any], calls: list[dict[str, Any]]
) -> bool:
    """Require evidence the coordinator only delegated the frozen task and waited."""
    if trace.get("root_tools_confined") is not True:
        return False
    receipt = trace.get("session_dispatch_evidence", {})
    workers = receipt.get("observations", [])
    if len(workers) != 1 or trace.get("coordinator_worker") != workers[0].get("thread_id"):
        return False
    if len(calls) != 1:
        return False
    call = calls[0]
    return (
        call.get("agent_type")
        == (entry["role"] if entry["arm"] == "named-worker" else GENERIC_ROLE)
        and call.get("fork_context", False) is False
        and isinstance(call.get("message"), str)
        and fingerprint(call["message"]) == entry["prompt_fingerprint"]
        and not call.get("items")
    )
