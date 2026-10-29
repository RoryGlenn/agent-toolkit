"""Existing benchmark plan/run integration for qualified large-project cases."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from benchmarks.files import read_regular
from benchmarks.large_projects.artifacts import freeze_delta, tree_hashes
from benchmarks.large_projects.deadline import progress, supervise
from benchmarks.large_projects.integration import (
    case_at,
    evaluate,
    seed_bundle,
    unpack_trusted,
    verify_bundle,
)
from benchmarks.large_projects.native import package_identity, preflight
from benchmarks.large_projects.resources import (
    Deadline,
    Limits,
    ResourceCell,
    checked_toolchains,
    require,
)
from benchmarks.large_projects.runner import environment, harness_hashes, verify_preparation
from benchmarks.runtime import NativeExecutor, config_text, digest, fingerprint, observe_trace


def load_context(path: Path, cases: list[str]) -> dict[str, Any]:
    """Bind plans to qualified current adapters and explicit, verified dependency inputs."""
    context: dict[str, Any] = json.loads(read_regular(path))
    context = {
        **context,
        "prepared": str(Path(context["prepared"]).resolve()),
        "qualification": str(Path(context["qualification"]).resolve()),
        "toolchains": [str(Path(p).resolve(strict=True)) for p in context["toolchains"]],
    }
    if not cases:
        raise ValueError("large-project plans require explicit case selection")
    from benchmarks.large_projects.qualification import GATES

    runtime_path = Path(context["runtime_qualification"]).resolve(strict=True)
    runtime = json.loads(read_regular(runtime_path))
    if (
        runtime.get("status") != "passed"
        or runtime.get("runner_hashes") != harness_hashes()
        or set(runtime.get("gates", {})) != GATES
        or any(g.get("status") != "passed" for g in runtime["gates"].values())
        or not runtime.get("cleanup", {}).get("complete")
    ):
        raise ValueError("complete current model-free runtime qualification is required")
    context.update(
        runtime_qualification=str(runtime_path),
        runtime_receipt_sha256=digest(runtime_path),
        native_package=runtime["native_package"],
    )
    context["dependencies"] = {
        case_id: str(Path(bundle).resolve(strict=True))
        for case_id, bundle in context.get("dependencies", {}).items()
    }
    receipts = {}
    dependencies = {}
    for case_id in cases:
        case = case_at(case_id)
        root = Path(context["qualification"]) / case_id
        report = json.loads(read_regular(root / "qualification.json"))
        expected_sides = (
            {"parent", "fixed", "alternative", "partial"}
            if case_id == "otel-queue-cancellation"
            else {"parent", "fixed"}
        )
        if (
            report.get("schema_version") != 2
            or report.get("status") != "qualified"
            or report.get("runner_hashes") != harness_hashes()
            or set(report.get("sides", {})) != expected_sides
            or any(
                s.get("status") != "qualified" or not s.get("commands")
                for s in report["sides"].values()
            )
            or not report.get("cleanup", {}).get("complete")
            or report.get("source_pins")
            != {k: case[k] for k in ("parent", "fixed", "test_patch_sha256")}
        ):
            raise ValueError(f"{case_id} has no complete current integrated qualification")
        hashes = json.loads(read_regular(root / "evidence-sha256.json"))
        for name, value in hashes.items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or digest(root / relative) != value:
                raise ValueError("qualification evidence changed")
        if "qualification.json" not in hashes:
            raise ValueError("qualification summary is not sealed")
        bundle = context.get("dependencies", {}).get(case_id)
        identity = verify_bundle(case, Path(bundle) if bundle else None)
        if any(side.get("dependencies") != identity for side in report["sides"].values()):
            raise ValueError("dependency inputs differ from the qualified evaluator")
        dependencies[case_id] = identity
        receipts[case_id] = digest(root / "evidence-sha256.json")
    context["qualification_receipts"] = receipts
    context["dependency_identities"] = dependencies
    limits = Limits(**context.get("limits", {}))
    limits.validate()
    if limits.memory_bytes != limits.filesystem_bytes:
        raise ValueError("native execution requires equal memory/allocated-filesystem ceilings")
    return context


def validate_context(plan: dict[str, Any]) -> None:
    """Revalidate selected preparation and receipts inside the attempt's wall watchdog."""
    context = plan["large_context"]
    if digest(Path(context["runtime_qualification"])) != context["runtime_receipt_sha256"]:
        raise ValueError("native runtime qualification changed since planning")
    for case_id in {e["case_id"] for e in plan["entries"]}:
        root = Path(context["qualification"]) / case_id
        if digest(root / "evidence-sha256.json") != context["qualification_receipts"][case_id]:
            raise ValueError("qualified context changed since planning")
        report = json.loads(read_regular(root / "qualification.json"))
        if report.get("runner_hashes") != harness_hashes() or report.get("status") != "qualified":
            raise ValueError("qualification no longer matches the running harness")
        bundle = context.get("dependencies", {}).get(case_id)
        actual = verify_bundle(case_at(case_id), Path(bundle) if bundle else None)
        if actual != context["dependency_identities"][case_id] or any(
            side.get("dependencies") != actual for side in report.get("sides", {}).values()
        ):
            raise ValueError("dependency inputs changed since qualification or planning")
        for name, value in json.loads(read_regular(root / "evidence-sha256.json")).items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or digest(root / relative) != value:
                raise ValueError("qualification evidence changed since planning")


def grade_record(case_id: str, evaluated: dict[str, Any]) -> dict[str, Any]:
    """Use the existing report schema; environment failure never becomes candidate failure."""
    environmental = evaluated["status"] == "environment_failure"
    failures = [
        r["name"]
        for r in evaluated["commands"]
        if r["status"] in {"behavior_mismatch", "candidate_build_failure"}
    ]
    if evaluated.get("artifact_failure"):
        failures.append(evaluated["artifact_failure"])
    passed = evaluated["status"] == "qualified"
    return {
        "case_id": case_id,
        "phase": 1,
        "status": "harness_error" if environmental else "needs_review" if passed else "failed",
        "failures": failures,
        "harness_error": "large-project environment failure" if environmental else None,
        "objective_complete": passed,
        "checks": [
            f"{r['name']}:{name}" for r in evaluated["commands"] for name in r.get("checks", {})
        ],
        "commands": evaluated["commands"],
        "needs_review": [
            "Independent blinded maintainability review of the frozen production delta"
        ],
        "evaluation": evaluated,
    }


def grade_artifact(
    case_id: str,
    artifact: Path,
    curator: Path,
    output: Path,
    toolchains: list[Path],
    bundle: Path | None,
    seconds: int,
) -> dict[str, Any]:
    """Model-free grading entrypoint; never executes candidate code in the controller."""
    case = case_at(case_id)

    def work(deadline: Deadline, owner: str) -> dict[str, Any]:
        verify_preparation(case, curator)
        frozen = output / "artifact"
        # Artifact inputs are controller-owned frozen deltas, never a live worker tree.
        before = tree_hashes(artifact)
        shutil.copytree(artifact, frozen, symlinks=True)
        if tree_hashes(frozen) != before or tree_hashes(artifact) != before:
            raise ValueError("artifact changed during transfer")
        evaluated = evaluate(
            case,
            curator,
            output / "grading",
            toolchains,
            deadline,
            owner,
            Limits(seconds=seconds),
            artifact=frozen,
            bundle=bundle,
        )
        return grade_record(case_id, evaluated)

    result = supervise(output, seconds, work)
    from benchmarks.__main__ import write_json

    write_json(output / "grade.json", result)
    return result


def run_attempt(
    plan: dict[str, Any], entry: dict[str, Any], root: Path, codex: Path, auth_source: Path | None
) -> dict[str, Any]:
    """Stage, verify, execute, freeze, destroy the actor, then independently rebuild/grade."""
    from benchmarks.__main__ import prepare, seal_result, verify_plan, verify_prompt_surface

    result: dict[str, Any] = {
        **{k: v for k, v in plan.items() if k != "entries"},
        **entry,
        "run_id": str(uuid.uuid4()),
        "status": "setup_error",
        "aggregate_tree_tokens": None,
        "cost": None,
    }
    context = plan["large_context"]
    limits = Limits(**{**context.get("limits", {}), "seconds": plan["wall_seconds"]})
    tools = [Path(p) for p in context["toolchains"]]
    case = case_at(entry["case_id"])
    curator = (Path(context["prepared"]) / case["id"]).resolve(strict=True)
    bundle_path = context.get("dependencies", {}).get(case["id"])
    bundle = Path(bundle_path) if bundle_path else None
    credential = root / "staging/client-home/auth.json"

    def work(deadline: Deadline, owner: str) -> dict[str, Any]:
        nonlocal result
        verify_plan(plan)
        validate_context(plan)
        verify_preparation(case, curator)
        if plan.get("budget_units") is None or plan["budget_units"] < 2:
            raise ValueError("large-project execution requires an aggregate descendant budget")
        if not auth_source or auth_source.is_symlink() or not auth_source.is_file():
            raise ValueError("run requires an explicitly selected regular auth.json")
        package = package_identity(codex)
        from benchmarks.cases import REPOSITORY

        checked_toolchains(
            [codex.parent.parent, *tools],
            [
                curator,
                Path(context["prepared"]),
                root,
                REPOSITORY,
                Path(context["qualification"]),
                *([bundle] if bundle else []),
            ],
        )
        if package != context["native_package"]:
            raise ValueError("native package differs from runtime qualification")
        stage = root / "staging"
        result = prepare(plan, entry, stage)
        progress(root, result)
        baseline = tree_hashes(stage / "workspace")
        state = stage / "workspace/.benchmark-state"
        for name in ("home", "tmp", "cache", "build"):
            (state / name).mkdir(parents=True, exist_ok=True)
        result["dependencies"] = seed_bundle(case, bundle, stage)
        if (stage / "cache").exists():
            shutil.copytree(stage / "cache", state / "cache", dirs_exist_ok=True, symlinks=True)
        env = environment(state, tools, network=False)
        env.update(HOME=str(stage / "actor-home"), TMPDIR=str(stage / "private-tmp"))
        if result["dependencies"].get("browser"):
            browser = result["dependencies"]["browser"]
            env["TOOLKIT_CHROMIUM_EXECUTABLE"] = browser["executable"]
            note = (
                "\n\nBrowser runtime: " + browser["version"] + ". For local Playwright calls, "
                "use chromium.launch({executablePath: "
                + json.dumps(browser["executable"])
                + "}). The default downloaded browser cache is absent in this explicit "
                "preinstalled mode. Network downloads are unavailable during execution.\n"
            )
            task = stage / "workspace/TASK.md"
            task.write_text(task.read_text() + note)
            prompt = stage / "prompt.txt"
            prompt.write_text(prompt.read_text() + note)
            result["prompt_fingerprint"] = fingerprint(prompt.read_text())
        config = config_text(
            stage / "workspace",
            stage / "actor-home",
            stage / "client-home",
            stage / "private-tmp",
            plan["model"],
            plan["effort"],
            plan["budget_units"],
            local_network=True,
            readonly_extra=[codex.parent.parent, *tools],
            shell_environment=env,
            project_guidance=True,
        )
        (stage / "client-home/config.toml").write_text(config)
        result["config_fingerprint"] = fingerprint(config)
        with ResourceCell(
            stage,
            limits,
            readonly=[codex.parent.parent, *tools],
            owner=owner,
            deadline=deadline,
            native_sandbox=True,
            client_transport=True,
        ) as cell:
            for name in ("workspace", "actor-home", "client-home", "private-tmp"):
                cell.upload(stage / name, stage / name)
            version = require(cell.execute([str(codex), "--version"]))
            if version.stdout.strip() != "codex-cli 0.165.0":
                raise ValueError("the integrated native runtime must be Codex CLI 0.165.0")
            result.update(native_package=package, codex_version=version.stdout.strip())
            result["isolation"] = preflight(
                cell,
                stage,
                codex,
                curator / "upstream-tests.patch",
                curator / "repository",
                case["fixed"],
                toolchains=tools,
                receipts=root / "preflight",
            )
            result["resources"] = cell.enforcement
            progress(root, result)
            shutil.copyfile(auth_source, credential)
            credential.chmod(0o600)
            cell.upload(credential, credential)
            executor = NativeExecutor(
                codex,
                stage / "client-home",
                stage / "actor-home",
                stage / "private-tmp",
                stage / "workspace",
            )

            def client(
                argv: list[str], cwd: Path, environment: dict[str, str], timeout: float
            ) -> Any:
                return cell.execute(argv, cwd, environment=environment, timeout=timeout)

            result["prompt_surface"] = verify_prompt_surface(executor, root, client)
            execution = cell.execute(
                [
                    str(codex),
                    "exec",
                    "--strict-config",
                    "--skip-git-repo-check",
                    "--json",
                    "--color",
                    "never",
                    "-C",
                    str(stage / "workspace"),
                    "-o",
                    str(stage / "client-home/final.txt"),
                    "-",
                ],
                stage / "workspace",
                environment=executor.environment,
                stdin=(stage / "prompt.txt").read_text(),
                timeout=deadline.remaining(),
            )
            result["execution"] = execution.to_dict()
            (root / "trace.jsonl").write_text(execution.stdout)
            (root / "stderr.txt").write_text(execution.stderr)
            result["memory_events"] = cell.events()
            result["status"] = (
                "timed_out"
                if execution.timed_out
                else "failed"
                if execution.returncode or execution.output_limited
                else "completed"
            )
            cell.freeze()
            progress(root, result)
            archive = root / "candidate.tar"
            cell.download(stage / "workspace", archive)
            # Native client sessions are protected from actor writes and contain no auth file.
            sessions = root / "sessions.tar"
            cell.download(stage / "client-home/sessions", sessions)
        # The actor and every detached child are dead before any hidden tests are staged.
        observed = root / "observed-client/sessions"
        unpack_trusted(sessions, observed, "sessions")
        sessions.unlink()
        result.update(observe_trace(execution.stdout, root / "observed-client"))
        freeze_delta(case["id"], archive, baseline, root / "artifact")
        archive.unlink()
        result["artifact_hashes"] = tree_hashes(root / "artifact")
        result["budget_accounting"] = {
            "limit_weighted_units": plan["budget_units"],
            "enforcement": "verified_native_shared_descendant_budget",
            "qualification": result["isolation"]["fingerprint"],
            "observed_units": None,
            "overshoot_units": None,
            "note": "Completion-boundary enforcement; actual attempt aggregate usage/cost "
            "unavailable unless emitted. Null is not zero.",
        }
        if result["status"] == "completed":
            progress(root, result)
            evaluated = evaluate(
                case,
                curator,
                root / "grading",
                tools,
                deadline,
                owner,
                limits,
                artifact=root / "artifact",
                bundle=bundle,
            )
            result["grade"] = grade_record(case["id"], evaluated)
            result["status"] = result["grade"]["status"]
        return result

    try:
        supervised = supervise(root, plan["wall_seconds"], work)
        result.update(supervised)
    finally:
        credential.unlink(missing_ok=True)
        seal_result(root, result)
    return result
