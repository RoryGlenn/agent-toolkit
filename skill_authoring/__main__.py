"""Scaffold skills with OpenAI and evaluate them using Anthropic's workflow on Codex."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from skill_authoring import UPSTREAM, workflow


def main() -> int:
    """Dispatch explicit local authoring operations; model runs require selected credentials."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify-upstream")
    scaffold = commands.add_parser("scaffold")
    scaffold.add_argument("name")
    scaffold.add_argument("--path", type=Path, required=True)
    scaffold.add_argument("--resources", default="")
    validate = commands.add_parser("validate")
    validate.add_argument("skill", type=Path)
    run = commands.add_parser("run")
    run.add_argument("evals", type=Path)
    run.add_argument("--skill", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--auth-source", type=Path, required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--effort", choices=["low", "medium", "high", "xhigh"], default="medium")
    run.add_argument("--repetitions", type=int, default=3)
    run.add_argument("--seconds", type=int, default=180)
    run.add_argument("--codex", default="codex")
    report = commands.add_parser("report")
    report.add_argument("output", type=Path)
    blind = commands.add_parser("blind")
    blind.add_argument("output", type=Path)
    blind.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        workflow.verify_upstream()
        if args.command == "verify-upstream":
            print("Pinned OpenAI and Anthropic files verified")
        elif args.command in ("scaffold", "validate"):
            script = (
                UPSTREAM
                / "openai/scripts"
                / ("init_skill.py" if args.command == "scaffold" else "quick_validate.py")
            )
            command = [sys.executable, str(script)]
            command += (
                [args.name, "--path", str(args.path), "--resources", args.resources]
                if args.command == "scaffold"
                else [str(args.skill)]
            )
            return subprocess.run(command, check=False).returncode
        elif args.command == "run":
            executable = shutil.which(args.codex)
            if executable is None:
                raise ValueError("Codex executable not found")
            plan = workflow.run(
                args.evals,
                args.skill,
                args.output,
                Path(executable).resolve(),
                args.auth_source,
                args.model,
                args.effort,
                args.repetitions,
                args.seconds,
            )
            print(json.dumps({"planned_runs": len(plan["runs"]), "output": str(args.output)}))
            failed = any(
                json.loads(workflow.read(args.output / r / "status.json"))["status"] != "completed"
                for r in plan["runs"]
            )
            return int(failed)
        elif args.command == "report":
            workflow.report(args.output.resolve())
            print(args.output / "review.html")
        elif args.command == "blind":
            workflow.blind(args.output.resolve(), args.destination.resolve())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
