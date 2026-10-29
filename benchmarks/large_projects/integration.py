"""Large-project adapters for the existing preparation, execution and grading workflow.

Only the controller reads the catalog and curator history. Actor cells receive an untouched
parent export and separately verified dependency inputs. A new cell rebuilds the frozen
production delta with sealed authoritative tests, after the actor cell is destroyed.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import tarfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

from benchmarks.files import read_regular
from benchmarks.large_projects.adapters import commands, manifest
from benchmarks.large_projects.artifacts import (
    apply_delta,
    fingerprint,
    freeze_delta,
    production,
    tree_hashes,
)
from benchmarks.large_projects.deadline import progress, supervise
from benchmarks.large_projects.export import export_parent
from benchmarks.large_projects.finalize import collector_control, finalize
from benchmarks.large_projects.prepare import CATALOG, git
from benchmarks.large_projects.resources import (
    Deadline,
    Limits,
    ResourceCell,
    checked_toolchains,
    require,
)
from benchmarks.large_projects.runner import (
    environment,
    harness_hashes,
    outcome,
    sha,
    verify_preparation,
    write_json,
)

DEPENDENCIES = {
    "otel-queue-cancellation": ("cache/go-mod",),
    "vscode-snippet-selections": (
        "workspace/node_modules",
        "workspace/build/node_modules",
        "cache/playwright",
    ),
}


def case_at(case_id: str) -> dict[str, Any]:
    """Resolve one versioned case; this function is never copied into an actor cell."""
    return next(case for case in json.loads(CATALOG.read_text())["cases"] if case["id"] == case_id)


def case_fingerprint(case_id: str) -> str:
    """Bind the source pins, task, grading contract and declared production component."""
    from benchmarks.large_projects.artifacts import SCOPES

    return fingerprint({"case": case_at(case_id), "grading": manifest(), "scope": SCOPES[case_id]})


def verify_version(name: str, output: str) -> None:
    """Reject a runnable but unsupported toolchain before it can qualify a case."""
    if name == "go-version" and not output.startswith("go version go1.26.0 "):
        raise ValueError("Go 1.26.0 is required")
    if name == "node-version" and output.strip() != "v22.22.1":
        raise ValueError("Node 22.22.1 is required")
    if name == "npm-version" and output.strip() != "10.9.4":
        raise ValueError("npm 10.9.4 is required")


def unpack_trusted(archive: Path, destination: Path, expected_root: str) -> None:
    """Materialize a trusted prefetch export, checking every archive path and link first.

    This is used only for dependency prefetch from the pinned parent, never actor output.
    Actor output is consumed by freeze_delta without archive extraction.
    """
    destination.mkdir(parents=True, exist_ok=False)
    seen: set[PurePosixPath] = set()
    links: list[tuple[Path, str]] = []
    total = 0
    with tarfile.open(archive, mode="r|*") as stream:
        for index, member in enumerate(stream):
            path = PurePosixPath(member.name)
            total += member.size
            if (
                index > 200_000
                or total > 4 * 1024**3
                or path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != expected_root
                or member.size < 0
                or path in seen
            ):
                raise ValueError("unsafe dependency archive")
            seen.add(path)
            relative = PurePosixPath(*path.parts[1:])
            if not relative.parts:
                continue
            target = destination / str(relative)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                content = stream.extractfile(member)
                if content is None:
                    raise ValueError("missing dependency content")
                with target.open("xb") as output:
                    shutil.copyfileobj(content, output, 1024**2)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
            elif member.issym():
                resolved = PurePosixPath(os.path.normpath(str(relative.parent / member.linkname)))
                if PurePosixPath(member.linkname).is_absolute() or ".." in resolved.parts:
                    raise ValueError("escaping dependency link")
                links.append((target, member.linkname))
            else:
                raise ValueError("dependency archive contains special or hardlinked data")
    # Links are last, so no archive write can traverse a link. Chained escapes also fail.
    for target, link in links:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(link)
    for target, _ in links:
        if not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError("chained dependency link escapes the bundle")


def verify_bundle(case: dict[str, Any], bundle: Path | None) -> dict[str, Any]:
    """Only source/dependency caches whose complete inventory matches may cross the boundary."""
    paths = DEPENDENCIES.get(case["id"], ())
    if not paths:
        return {"required": False}
    if bundle is None:
        raise ValueError("this case requires a separately prefetched dependency bundle")
    receipt = json.loads(read_regular(bundle / "dependencies.json"))
    if receipt.get("case_id") != case["id"] or receipt.get("parent") != case["parent"]:
        raise ValueError("dependency bundle belongs to another source pin")
    if receipt.get("status") != "prefetched" or set(receipt.get("paths", [])) != set(paths):
        raise ValueError("dependency prefetch did not complete")
    actual = tree_hashes(bundle / "inputs")
    if actual != receipt.get("hashes"):
        raise ValueError("dependency bundle inventory changed")
    # No Go compilation cache, source tree, Git objects or curator outputs are exported.
    if any(
        not any(name == path or name.startswith(path + "/") for path in paths) for name in actual
    ):
        raise ValueError("dependency bundle contains undeclared inputs")
    return {
        "required": True,
        "receipt_sha256": sha(bundle / "dependencies.json"),
        "input_fingerprint": fingerprint(actual),
    }


def seed_bundle(case: dict[str, Any], bundle: Path | None, stage: Path) -> dict[str, Any]:
    """Copy only declared verified dependency inputs; compilation always starts cold."""
    receipt = verify_bundle(case, bundle)
    if bundle is not None and receipt["required"]:
        for relative in DEPENDENCIES[case["id"]]:
            shutil.copytree(bundle / "inputs" / relative, stage / relative, symlinks=True)
    return receipt


def prefetch(
    case: dict[str, Any], curator: Path, output: Path, toolchains: list[Path], seconds: int = 1800
) -> dict[str, Any]:
    """Fetch dependencies from the untouched parent in a separate bounded network phase."""
    limits = Limits(seconds=seconds)

    def work(deadline: Deadline, owner: str) -> dict[str, Any]:
        from benchmarks.cases import REPOSITORY

        checked_toolchains(toolchains, [curator, output, REPOSITORY])
        verify_preparation(case, curator)
        stage = output / "staging"
        stage.mkdir()
        export_parent(case, curator, stage / "workspace")
        for name in ("home", "tmp", "cache", "build"):
            (stage / name).mkdir()
        cellroot = output / "cell"
        inside = cellroot / "input"
        records = []
        with ResourceCell(
            cellroot,
            limits,
            readonly=toolchains,
            deadline=deadline,
            owner=owner,
            client_transport=True,
        ) as cell:
            cell.upload(stage, inside)
            env = environment(inside, toolchains, network=True)
            # Docker already has the platform's reachable proxy defaults. Do not replace
            # them with an outer-only hostname; only explicit CA paths need mounting.
            env = {k: v for k, v in env.items() if "proxy" not in k.lower()}
            for command in commands(case["id"], inside / "workspace", inside / "build", "fixed"):
                if not (
                    command.name.startswith("dependencies")
                    or command.name in {"browser", "go-version", "node-version", "npm-version"}
                ):
                    continue
                result = cell.execute(
                    command.argv, command.cwd, environment=env, timeout=command.timeout
                )
                records.append({"name": command.name, **result.to_dict()})
                write_json(output / f"command-{command.name}.json", records[-1])
                require(result)
                verify_version(command.name, result.stdout)
            paths = DEPENDENCIES.get(case["id"], ())
            # Export only source dependencies. No source/build/home/trace tree is retained.
            cell.freeze()
            inputs = output / "inputs"
            inputs.mkdir()
            for relative in paths:
                raw = output / (relative.replace("/", "-") + ".tar")
                cell.download(inside / relative, raw)
                unpack_trusted(raw, inputs / relative, Path(relative).name)
                raw.unlink()
        receipt = {
            "status": "prefetched",
            "case_id": case["id"],
            "parent": case["parent"],
            "paths": list(paths),
            "hashes": tree_hashes(inputs),
            "commands": records,
        }
        write_json(output / "dependencies.json", receipt)
        return receipt

    return supervise(output, seconds, work)


def evaluator_command(
    cell: ResourceCell,
    argv: list[str],
    cwd: Path,
    source: Path,
    case_id: str,
    phase: str,
    name: str,
    env: dict[str, str],
    timeout: float,
) -> Any:
    """Seal all source/test/build inputs, permitting only declared generated files.

    The evaluator has its own PID and network namespace. The actor no longer exists.
    Readonly mounts inherited by descendants cannot be made writable in another userns.
    """
    command = [
        "/usr/bin/bwrap",
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(cell.root),
        str(cell.root),
        "--bind",
        "/tmp",
        "/tmp",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
    ]
    if case_id == "vscode-snippet-selections" and name == "transpile":
        # The transpiler replaces out/ itself. Seal every immutable input individually.
        result = require(
            cell.execute(
                ["/usr/bin/find", str(source), "-mindepth", "1", "-maxdepth", "1"], timeout=10
            )
        )
        for entry in result.stdout.splitlines():
            if Path(entry).name != "out":
                command += ["--ro-bind", entry, entry]
    else:
        command += ["--ro-bind", str(source), str(source)]
    command += ["--chdir", str(cwd), "--clearenv"]
    for key, value in env.items():
        command += ["--setenv", key, value]
    # docker exec's transient shim can disappear while Bubblewrap installs its
    # parent-death signal. Keep a visible trusted parent alive until the sandbox exits.
    launch = [
        "/usr/bin/python3",
        "-I",
        "-B",
        "-c",
        "import subprocess,sys; sys.exit(subprocess.run(sys.argv[1:]).returncode)",
    ]
    return cell.execute([*launch, *command, "--", *argv], cwd, timeout=timeout)


def evaluate(
    case: dict[str, Any],
    curator: Path,
    output: Path,
    toolchains: list[Path],
    deadline: Deadline,
    owner: str,
    limits: Limits,
    *,
    artifact: Path | None = None,
    side: str = "fixed",
    bundle: Path | None = None,
    expected_side: str | None = None,
) -> dict[str, Any]:
    """Rebuild one frozen candidate or trusted control against the same finalized checks."""
    output.mkdir(parents=True, exist_ok=False)
    from benchmarks.cases import REPOSITORY

    toolchains = checked_toolchains(
        toolchains, [curator, output, REPOSITORY, *([bundle] if bundle else [])]
    )
    started = time.monotonic()
    stage = output / "staging"
    stage.mkdir()
    source = stage / "workspace"
    selected = {
        **case,
        "parent": case["fixed"] if side == "fixed" and artifact is None else case["parent"],
    }
    export_parent(selected, curator, source)
    if artifact is not None:
        apply_delta(case["id"], artifact, source)
    # Immutable tests always replace candidate-authored tests, from the verified pin.
    for name in case["test_paths"]:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git(curator / "repository", "show", f"{case['fixed']}:{name}"))
    adapted = finalize(case["id"], source)
    if artifact is None and side in {"alternative", "partial"}:
        collector_control(source, side)
    input_hashes = {
        name: sha(source / name) for name in case["test_paths"] if (source / name).is_file()
    }
    adapted_hashes = {str(p.relative_to(source)): sha(p) for p in adapted}
    for name in ("home", "tmp", "cache", "build"):
        (stage / name).mkdir()
    dependencies = seed_bundle(case, bundle, stage)
    cellroot = output / "cell"
    inside = cellroot / "input"
    insource, build = inside / "workspace", inside / "build"
    records = []
    status = "environment_failure"
    setup_seconds = test_seconds = 0.0
    with ResourceCell(
        cellroot, limits, readonly=toolchains, owner=owner, deadline=deadline, native_sandbox=True
    ) as cell:
        cell.upload(stage, inside)
        env = environment(inside, toolchains, network=False)
        for toolchain in toolchains:
            if (toolchain / "share/bison").is_dir():
                env["BISON_PKGDATADIR"] = str(toolchain / "share/bison")
        plan = commands(
            case["id"], insource, build, expected_side or (side if artifact is None else "fixed")
        )
        plan = [c for c in plan if not (c.name.startswith("dependencies") or c.name == "browser")]
        for index, command in enumerate(plan):
            if command.parser == "postgres" and command.name.startswith(
                ("controls-", "regressions-")
            ):
                require(cell.execute(["/bin/mkdir", "-p", str(build / command.name)]))
            command_env = dict(env)
            if command.parser == "postgres" and command.name.startswith("regressions-"):
                command_env["TOOLKIT_SQLSTATE"] = "1"
            result = evaluator_command(
                cell,
                command.argv,
                command.cwd,
                insource,
                case["id"],
                command.phase,
                command.name,
                command_env,
                command.timeout,
            )

            def read_text(path: Path) -> str:
                return require(cell.execute(["/bin/cat", str(path)], timeout=10)).stdout

            status, checks = outcome(command, result, read_text)
            if status == "passed":
                verify_version(command.name, result.stdout)
            record = {
                **result.to_dict(),
                "name": command.name,
                "phase": command.phase,
                "cwd": str(command.cwd),
                "environment": command_env,
                "status": status,
                "checks": checks,
                "expected": command.expected,
            }
            records.append(record)
            write_json(output / f"{index:02d}-{command.name}.json", record)
            if command.phase == "setup":
                setup_seconds += result.elapsed_seconds
            else:
                test_seconds += result.elapsed_seconds
            if status == "environment_failure":
                break
        events = cell.events()
        enforcement = cell.enforcement
        complete = len(records) == len(plan) and all(
            r["status"] in {"qualified", "passed"} for r in records
        )
        status = (
            "qualified"
            if complete
            else "environment_failure"
            if any(r["status"] == "environment_failure" for r in records)
            else "behavior_mismatch"
        )
    result = {
        "status": status,
        "commands": records,
        "cold_setup_seconds": setup_seconds,
        "warm_test_seconds": test_seconds,
        "elapsed_seconds": time.monotonic() - started,
        "test_hashes": input_hashes,
        "adapted_test_hashes": adapted_hashes,
        "resources": enforcement,
        "memory_events": events,
        "dependencies": dependencies,
        "sealed_inputs": "readonly source and authoritative tests in a separate namespace",
    }
    write_json(output / "evaluation.json", result)
    return result


def control_artifact(
    case: dict[str, Any],
    curator: Path,
    output: Path,
    side: str,
    deadline: Deadline,
    owner: str,
    limits: Limits,
) -> Path:
    """Exercise the real freeze/transfer path using a trusted model-free source writer.

    Only this control writer is supplied reference production bytes. No agent is launched;
    no added hidden tests, history, curator caches or solution metadata enter its cell.
    """
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    export_parent(case, curator, workspace)
    baseline = tree_hashes(workspace)
    if side == "fixed":
        changed = git(curator / "repository", "diff", "--name-only", case["parent"], case["fixed"])
        for name in changed.decode().splitlines():
            if production(case["id"], name):
                (workspace / name).write_bytes(
                    git(curator / "repository", "show", f"{case['fixed']}:{name}")
                )
    elif side in {"alternative", "partial"}:
        collector_control(workspace, side)
    cellroot = output / "cell"
    raw = output / "candidate.tar"
    with ResourceCell(cellroot, limits, owner=owner, deadline=deadline) as cell:
        cell.upload(workspace, cellroot / "workspace")
        cell.freeze()
        cell.download(cellroot / "workspace", raw)
    artifact = output / "artifact"
    freeze_delta(case["id"], raw, baseline, artifact)
    raw.unlink()
    write_json(output / "artifact-sha256.json", tree_hashes(artifact))
    return artifact


def qualify_integrated(
    case: dict[str, Any],
    curator: Path,
    output: Path,
    toolchains: list[Path],
    seconds: int = 7200,
    bundle: Path | None = None,
) -> dict[str, Any]:
    """Run all trusted sides through the exact candidate evaluator, under one watchdog."""
    initial_hashes = harness_hashes()
    report: dict[str, Any] = {
        "schema_version": 2,
        "case_id": case["id"],
        "platform": platform.platform(),
        "manifest_sha256": sha(CATALOG),
        "adapter_contract": manifest(),
        "runner_hashes": initial_hashes,
        "source_pins": {key: case[key] for key in ("parent", "fixed", "test_patch_sha256")},
        "wall_seconds": seconds,
        "wall_scope": "staging-inclusive shared external deadline",
        "compiler_workers": 2,
        "ready_for_model_comparison": False,
        "sides": {},
        "status": "environment_failure",
    }

    def work(deadline: Deadline, owner: str) -> dict[str, Any]:
        verify_preparation(case, curator)
        for side in (
            ("parent", "fixed", "alternative", "partial")
            if case["id"] == "otel-queue-cancellation"
            else ("parent", "fixed")
        ):
            report["sides"][side] = {"status": "not_started", "commands": []}
        for side in report["sides"]:
            artifact = control_artifact(
                case,
                curator,
                output / f"{side}-actor",
                side,
                deadline,
                owner,
                Limits(seconds=seconds),
            )
            report["sides"][side] = evaluate(
                case,
                curator,
                output / side,
                toolchains,
                deadline,
                owner,
                Limits(seconds=seconds),
                side=side,
                bundle=bundle,
                artifact=artifact,
                expected_side=side,
            )
            write_json(output / f"qualification.{side}.partial.json", report)
            progress(output, report)
        report["status"] = (
            "qualified"
            if all(s["status"] == "qualified" for s in report["sides"].values())
            else "not_qualified"
        )
        if harness_hashes() != initial_hashes:
            report.update(status="environment_failure", error="runner changed during qualification")
        return report

    supervised = supervise(output, seconds, work)
    report.update(supervised)
    write_json(output / "qualification.json", report)
    paths = [output / "qualification.json", *output.glob("*/*.json")]
    write_json(output / "evidence-sha256.json", {str(p.relative_to(output)): sha(p) for p in paths})
    return report
