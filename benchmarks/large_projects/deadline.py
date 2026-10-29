"""An external watchdog includes source validation, staging, execution and grading."""

from __future__ import annotations

import json
import multiprocessing
import os
import signal
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from benchmarks.files import read_regular
from benchmarks.large_projects.resources import Deadline, cleanup_owned


class AttemptExpired(TimeoutError):
    """The external owner stopped active work at the shared deadline."""


def progress(root: Path, result: dict[str, Any]) -> None:
    """Keep controller evidence even if a subsequent phase blocks or is killed."""
    temporary = root / "progress.partial"
    temporary.write_text(json.dumps(result, sort_keys=True) + "\n")
    temporary.replace(root / "progress.json")


def previous(root: Path) -> dict[str, Any]:
    """Read only controller-created checkpoints, never a file in either execution cell."""
    path = root / "progress.json"
    if path.exists():
        value: dict[str, Any] = json.loads(read_regular(path))
        return value
    return {}


def supervise(
    root: Path, seconds: float, work: Callable[[Deadline, str], dict[str, Any]]
) -> dict[str, Any]:
    """Kill even a blocked staging worker; cleanup is bounded separately from active work.

    The worker's status file is controller-owned and never mounted into either cell.
    Container ownership labels let the external watchdog remove escaped/detached descendants
    even when the worker cannot run its own finally blocks. No model credentials are needed.
    """
    if not 0 < seconds <= 14400:
        raise ValueError("attempt seconds must be in (0, 14400]")
    deadline = Deadline(seconds)
    root.mkdir(parents=True, exist_ok=False)
    owner = str(uuid.uuid4())
    record = root / "worker-result.json"

    def interrupted(_signal: int, _frame: Any) -> None:
        raise AttemptExpired("external staging-inclusive deadline expired")

    def worker() -> None:
        os.setsid()
        signal.signal(signal.SIGTERM, interrupted)
        try:
            result = work(deadline, owner)
        except TimeoutError as exc:
            result = {**previous(root), "status": "timed_out", "error": str(exc)}
        except BaseException as exc:
            saved = previous(root)
            result = {
                **saved,
                "status": "harness_error" if "execution" in saved else "setup_error",
                "error": f"{type(exc).__name__}: {exc}",
            }
        temporary = record.with_suffix(".partial")
        temporary.write_text(json.dumps(result, sort_keys=True) + "\n")
        temporary.replace(record)

    process = multiprocessing.get_context("fork").Process(target=worker)
    timed_out = False
    cancelled = False
    result: dict[str, Any] = {}
    started = time.monotonic()
    process.start()
    try:
        process.join(max(0, deadline.expires - time.monotonic()))
        timed_out = process.is_alive()
    except KeyboardInterrupt:
        cancelled = True
    finally:
        if process.is_alive():
            process.terminate()
            process.join(1)
        if process.is_alive():
            try:
                if process.pid is not None:
                    os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.kill()
            process.join(5)
        if record.is_file():
            result = json.loads(read_regular(record))
        else:
            result = previous(root)
        if timed_out or cancelled:
            result.update(status="cancelled" if cancelled else "timed_out")
        elif not result or process.exitcode:
            result = {"status": "harness_error", "error": "attempt worker did not complete"}
        active_elapsed = time.monotonic() - started
        cleanup = cleanup_owned(owner)
        result.update(
            {
                "owner": owner,
                "staging_inclusive_seconds": seconds,
                "active_elapsed_seconds": active_elapsed,
                "cleanup": cleanup,
                "total_elapsed_seconds": time.monotonic() - started,
            }
        )
        if not cleanup["complete"]:
            result["status"] = "harness_error"
        (root / "supervision.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
