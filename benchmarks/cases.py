"""Versioned public contracts and curator-owned development controls."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent

COMMON = """
Work only in this supplied RecordBatch project using Python 3.11+ and the standard library.
This is a source snapshot with no Git repository or history. Inspect files directly;
Git is available for explicit file comparisons, not repository status or historical diffs.
Do not access benchmark infrastructure, other checkouts, personal files, or the network.
Preserve the existing CLI: python recordbatch.py --db FILE request '<JSON object>'.
Responses are JSON objects with ok and job/jobs/results/value/output or error fields.
Store(path, principal) authorizes tenant operations: principal must equal tenant. Successful
submission accepts asynchronous work with state queued; completion is a separate operation.
A tenant has capacity one. Canonical payload equality ignores dictionary key order. Job IDs
are opaque integers, stable after retry/restart. Distinct request identities are distinct jobs.
Existing submit/status/delete/effect/ack/cleanup/cancel/complete/resume/render behavior must
remain compatible except for changes requested below. A storage failure is never success.
The public fault seams fault='insert'/'transition' raise a storage failure inside the
transaction; effect fault='before_commit'/'after_commit' exits the process with code 75 at
that boundary. Retain these neutral seams so failure recovery can be tested.
SQLite file/transaction/process-restart guarantees only; do not promise distributed,
PostgreSQL, filesystem power-loss, or provider exactly-once guarantees.
Deliver working source, regression tests if behavior changes, and applicable README updates.
Do not report your own work as a benchmark score. No external dependency installation.
""".strip()

DOCS = """
Do not modify recordbatch.py or build.py. README.md must include runnable examples in fenced
`recordbatch` blocks. Each block is a JSON object with steps, a nonempty list of objects:
{"argv":["python","recordbatch.py","--db","quickstart.sqlite","request","{...}"],
 "expect":{"ok":true}}. `expect` is an exact JSON response, or a recursively matched subset
when `subset` is true. Paths must be relative to the project and databases must end .sqlite.
Use python build.py to build and python recordbatch.pyz for archive examples. Build steps
have expect_exit:0 and omit expect. Examples execute in order from a fresh project copy;
databases start absent except upgrade.sqlite, which is a documented seeded schema-v1 DB
with tenant legacy, key retained, payload {"value":7}, job id 41, state queued. Include an
example demonstrating that upgrade preserves this job. An example can declare expect_exit:2
for invalid JSON input, then demonstrate recovery with a valid request. Explain prerequisites,
working directory, expected outcome, and errors in prose. Executable checks do not grade
reader clarity or the truth/completeness of other prose; those require independent review.
""".strip()


@dataclass(frozen=True)
class Case:
    """One public task and its versioned objective oracle."""

    id: str
    family: str
    difficulty: str
    title: str
    requirement: str
    review: tuple[str, ...] = ()
    version: str = "1"

    @property
    def task(self) -> str:
        """Return the complete actor-visible contract."""
        extra = "\n\n" + DOCS if self.family == "docs" else ""
        return f"# {self.id}: {self.title}\n\n{COMMON}\n\n{self.requirement}{extra}\n"

    @property
    def fingerprint(self) -> str:
        """Identify the task, fixture, and oracle version without using model output."""
        digest = hashlib.sha256(self.task.encode())
        for path in sorted((ROOT / "recordbatch").glob("*")):
            if path.is_file() and path.suffix in {".py", ".md"}:
                digest.update(path.name.encode() + path.read_bytes())
        digest.update((ROOT / "oracles.py").read_bytes())
        digest.update((ROOT / "cases.py").read_bytes())
        return digest.hexdigest()

    def manifest(self) -> dict[str, Any]:
        """Return serializable task metadata."""
        return {
            **asdict(self),
            "fingerprint": self.fingerprint,
            "public_development": True,
            "difficulty_calibrated": False,
        }


CASES = (
    Case(
        "ddia-easy",
        "ddia",
        "easy",
        "Tenant-scoped request identity",
        "Fix submit: repeat (tenant,key,payload) returns the same job, even at full capacity. "
        "Same tenant/key with different payload returns conflict. The same key in another "
        "tenant is independent. Different keys with identical payload remain distinct once "
        "capacity is available. Authentication must still be enforced.",
    ),
    Case(
        "ddia-medium",
        "ddia",
        "medium",
        "Atomic capacity admission",
        "Fix submit so concurrent independent processes/connections admit at most one job "
        "per capacity-one tenant. Reservation and job insertion are one atomic operation. "
        "An insertion failure rolls back reservation. A subsequent valid submit succeeds. "
        "Different tenants proceed independently; avoid application-level barriers.",
    ),
    Case(
        "ddia-hard",
        "ddia",
        "hard",
        "Durable effect identity across replay",
        "Fix effect(tenant,event_id,delta,fault='') so a database balance changes once per "
        "business identity across concurrent duplicates, actual process exits before commit "
        "and after commit before ack, restart, ack, cleanup, and deliberate replay AFTER "
        "cleanup. Acknowledged events may replay indefinitely. Distinct event IDs carrying "
        "the same delta still apply. Keep ack/cleanup as receipt maintenance operations.",
    ),
    Case(
        "design-easy",
        "design",
        "easy",
        "Idempotent deletion with honest errors",
        "Fix delete(tenant,id): an already absent job is success. Keep the actual authorization "
        "wrapper; denial must raise PermissionError (CLI forbidden) even if the ID is absent. "
        "SQLite storage failures must propagate (CLI storage), never become absence/success.",
    ),
    Case(
        "design-medium",
        "design",
        "medium",
        "Complete batch submission API",
        "Implement Store.submit_many(tenant, requests) for arbitrary finite iterables, including "
        "empty iterators and one-shot generators. Each item has key/payload. Return one ordered "
        "{ok:true,job:...} or {ok:false,error:...} result per item, continuing after capacity or "
        "conflict/storage errors. Authorize before iteration; forbidden access raises "
        "PermissionError. Preserve submit and the submit_many CLI. Callers should not manage "
        "connections, reservation, or transaction internals.",
        ("Does the API hide transaction and iteration obligations without needless machinery?",),
    ),
    Case(
        "design-hard",
        "design",
        "hard",
        "Extend the output boundary",
        "Extend render(jobs, adapter='json') with csv. Preserve byte-compatible JSON behavior "
        "and unknown_adapter errors. CSV uses the standard quoting rules, header "
        "id,tenant,key,state, and preserves input order, empty inputs, commas/quotes/newlines. "
        "Keep Store and CLI clients compatible. A separately supplied fresh-maintainer task "
        "will add a second adapter using a different input representation after this artifact "
        "is frozen; do not implement unspecified adapters speculatively.",
        ("Independent fresh maintainer: assess boundary/caller obligations after the sequel.",),
    ),
    Case(
        "docs-easy",
        "docs",
        "easy",
        "A working newcomer quickstart",
        "Replace the sparse README with a newcomer quickstart that creates a job and checks "
        "its queued status in a fresh database. Include executable examples for init, submit, "
        "and status. Do not imply acceptance means completion.",
        ("Can a fresh reader reach the checked outcome without unstated knowledge?",),
    ),
    Case(
        "docs-medium",
        "docs",
        "medium",
        "Document the asynchronous contract",
        "Document acceptance versus completion, status, retry identity/conflict, capacity, tenant "
        "authorization, and storage errors using only implemented guarantees. Include executable "
        "examples showing queued acceptance, explicit complete then completed status, identical "
        "retry, conflicting retry, capacity rejection, and forbidden cross-tenant access.",
        ("Fact review: acceptance, completion, retries, tenant and errors match source.",),
    ),
    Case(
        "docs-hard",
        "docs",
        "hard",
        "Archive-only install, recovery, and upgrade",
        "Write a release/consumer procedure with runnable examples to build recordbatch.pyz, "
        "then use ONLY that archive in a fresh consumer directory. Show an invalid-JSON failure "
        "and successful recovery. Upgrade the supplied schema-v1 upgrade.sqlite and verify "
        "job 41 is retained; document Python prerequisites and supported SQLite guarantees.",
        ("Fresh consumer: follow archive install/recovery/upgrade and assess usability.",),
    ),
    Case(
        "integrated-easy",
        "integrated",
        "easy",
        "Tenant-scoped status filter",
        "Add optional state to Store.status(tenant,state=None) and CLI status requests. None "
        "preserves all old tenant-only results. Valid states queued/running/completed/cancelled "
        "filter within that tenant; other values return invalid_state. Preserve authorization, "
        "update README examples and tests.",
        ("Docs accurately explain filter and compatibility.",),
    ),
    Case(
        "integrated-medium",
        "integrated",
        "medium",
        "Cancel and resume without capacity drift",
        "Fix transition cancellation/completion/resumption. Concurrent cancel and complete have "
        "one terminal winner; neither overwrites a terminal state. Repeated cancel/complete "
        "release capacity at most once. Resume cancelled jobs reserves capacity atomically and "
        "returns queued; resume completed returns completed error. The transition fault rolls "
        "back both job and reservation. Behavior persists across restart. Build a working "
        "archive and document these guarantees and errors.",
        ("Package and cancellation documentation match tested behavior.",),
    ),
    Case(
        "integrated-hard",
        "integrated",
        "hard",
        "Honest uncertain external delivery",
        "Implement Store.deliver(tenant,delivery_id,provider), where provider is a callable with "
        "no deduplication/query operation: normal return acknowledges an effect, TimeoutError "
        "gives no evidence whether an effect occurred, and ValueError is a known-before-effect "
        "rejection. Persist delivered/unknown/rejected state. Two identical observable timeouts "
        "may have different actual effects; both must remain durable unknown, requiring external "
        "reconciliation. Never blindly retry unknown or delivered, including concurrent calls "
        "or restart; retry of rejected is permitted. A process exit around a provider call must "
        "not allow blind retry. Enforce tenant isolation, package it, and document the operator "
        "reconciliation boundary without promising impossible exactly-once delivery.",
        ("Docs explain uncertainty, reconciliation and supported guarantees accurately.",),
    ),
)

SEQUEL = """# Fresh-maintainer sequel (design-hard, phase 2)
The phase-1 artifact is frozen. As a fresh maintainer, extend its render boundary with ndjson.
Accept both the old flat job dictionaries and a new nested mapping representation:
{"identity":{"id":7,"tenant":"a","key":"k"},"status":"queued","data":{"x":1}}.
Normalize new records to the existing flat public job representation for every adapter.
Accept arbitrary finite iterables, including one-shot generators. ndjson is one JSON object
per line, with a final newline for nonempty input and empty string for empty input. Preserve
JSON and CSV contracts, input order, errors and CLI behavior. Document caller obligations.
The reviewer will separately assess how much client/implementation knowledge this change
requires; there are no line-count, class-count, or keyword quality scores.
"""


def get_case(case_id: str) -> Case:
    """Resolve a public case identifier or fail explicitly."""
    for case in CASES:
        if case.id == case_id:
            return case
    raise ValueError(f"unknown case: {case_id}")


def replace_once(text: str, before: str, after: str) -> str:
    """Apply a reviewed control mutation while detecting fixture drift."""
    if text.count(before) != 1:
        raise ValueError(f"control anchor is not unique: {before[:70]!r}")
    return text.replace(before, after, 1)


def defect(source: str, case_id: str) -> str:
    """Introduce one substantive wrong control, also used as the starting defect."""
    changes = {
        "ddia-easy": (
            '"SELECT * FROM jobs WHERE tenant=? AND request_id=?", (tenant, key)',
            '"SELECT * FROM jobs WHERE request_id=?", (key,)',
        ),
        "ddia-medium": (
            'if fault == "insert":\n                raise sqlite3.IntegrityError',
            'if fault == "insert":\n                connection.commit()\n'
            "                raise sqlite3.IntegrityError",
        ),
        "ddia-hard": (
            'connection.execute("DELETE FROM inbox WHERE tenant=? AND acked=1", (tenant,))',
            'connection.execute("DELETE FROM effects WHERE tenant=?", (tenant,))\n'
            "            connection.execute("
            '"DELETE FROM inbox WHERE tenant=? AND acked=1", (tenant,))',
        ),
        "design-easy": (
            "if row is None:\n                return",
            'if row is None:\n                raise ValueError("not_found")',
        ),
        "design-medium": (
            "for request in requests:",
            "for index in range(len(requests)):\n            request = requests[index]",
        ),
        "design-hard": ('if adapter == "csv":', 'if adapter == "csv_DISABLED":'),
        "integrated-easy": ("(tenant, state, state),", "(tenant, None, None),"),
        "integrated-medium": (
            'if state not in {"completed", "cancelled"}:',
            'if action in {"cancel", "complete"}:',
        ),
        "integrated-hard": (
            'state = "unknown"\n        except ValueError:',
            'state = "delivered"\n        except ValueError:',
        ),
    }
    if case_id not in changes:
        return source
    return replace_once(source, *changes[case_id])


def sequel_reference(source: str) -> str:
    """Extend the trusted reference with the independently specified second adapter."""
    return replace_once(
        source,
        '    if adapter == "json":\n',
        """    jobs = [
        {"id": row["identity"]["id"], "tenant": row["identity"]["tenant"],
         "key": row["identity"]["key"], "state": row["status"], "payload": row["data"]}
        if "identity" in row else row for row in jobs
    ]
    if adapter == "ndjson":
        return "".join(json.dumps(row, sort_keys=True) + "\\n" for row in jobs)
    if adapter == "json":
""",
    )


def example(
    request: dict[str, Any],
    expect: dict[str, Any],
    db: str = "quickstart.sqlite",
    archive: bool = False,
    exit_code: int = 0,
) -> dict[str, Any]:
    """Construct a directly executable documentation example."""
    return {
        "argv": [
            "python",
            "recordbatch.pyz" if archive else "recordbatch.py",
            "--db",
            db,
            "request",
            json.dumps(request),
        ],
        "expect": expect,
        "subset": True,
        "expect_exit": exit_code,
    }


def reference_readme(case_id: str) -> str:
    """Return a working original procedure; prose quality still needs independent review."""
    steps = [
        example({"op": "init"}, {"ok": True}),
        example(
            {"op": "submit", "key": "first", "payload": {"value": 7}},
            {"ok": True, "job": {"state": "queued"}},
        ),
        example(
            {"op": "status"},
            {
                "ok": True,
                "jobs": [
                    {
                        "id": 1,
                        "tenant": "demo",
                        "key": "first",
                        "payload": {"value": 7},
                        "state": "queued",
                    }
                ],
            },
        ),
    ]
    if case_id == "docs-medium":
        steps += [
            example(
                {"op": "submit", "key": "first", "payload": {"value": 7}},
                {"ok": True, "job": {"id": 1}},
            ),
            example(
                {"op": "submit", "key": "first", "payload": {"value": 8}},
                {"ok": False, "error": "conflict"},
            ),
            example(
                {"op": "submit", "key": "second", "payload": {}}, {"ok": False, "error": "capacity"}
            ),
            example(
                {"op": "status", "tenant": "demo", "principal": "other"},
                {"ok": False, "error": "forbidden"},
            ),
            example({"op": "complete", "id": 1}, {"ok": True, "job": {"state": "completed"}}),
            example(
                {"op": "status"},
                {
                    "ok": True,
                    "jobs": [
                        {
                            "id": 1,
                            "tenant": "demo",
                            "key": "first",
                            "payload": {"value": 7},
                            "state": "completed",
                        }
                    ],
                },
            ),
        ]
    if case_id == "docs-hard":
        steps = [
            {"argv": ["python", "build.py"], "expect_exit": 0},
            {
                "argv": ["python", "recordbatch.pyz", "--db", "fresh.sqlite", "request", "{"],
                "expect_exit": 2,
                "expect": {"ok": False},
                "subset": True,
            },
            example({"op": "init"}, {"ok": True}, "fresh.sqlite", True),
            example(
                {"op": "submit", "key": "consumer", "payload": {}},
                {"ok": True, "job": {"state": "queued"}},
                "fresh.sqlite",
                True,
            ),
            example(
                {"op": "status", "tenant": "legacy"},
                {
                    "ok": True,
                    "jobs": [
                        {
                            "id": 41,
                            "tenant": "legacy",
                            "key": "retained",
                            "payload": {"value": 7},
                            "state": "queued",
                        }
                    ],
                },
                "upgrade.sqlite",
                True,
            ),
        ]
    return (
        """# RecordBatch consumer guide

Requires Python 3.11 or later with SQLite, no third-party packages. Start in the extracted
project directory. The examples below are executable request/expected-result pairs; run
the argv as a command, quoting the final JSON argument as one shell argument.

Submission accepts queued asynchronous work; it does not finish the job. Poll status and
use complete only when processing has finished. Retrying the same tenant/key and payload
returns its original job; a changed payload is conflict. Capacity is one active job per
tenant, so a second identity may be rejected until capacity is released. principal is the
authenticated tenant and a mismatch is forbidden. Storage failures return storage and are
not successful completion. There is no distributed or power-loss guarantee.

To distribute, run python build.py and copy only recordbatch.pyz into a new consumer
directory; invoke it with Python. An invalid JSON request exits 2 without applying work.
Correct the JSON and retry. Existing schema-v1 databases upgrade on open; keep the retained
job's identity, payload and state. The upgrade example starts from the documented seeded DB.
Cancellation and completion serialize: the first terminal transition wins. Repetition
releases no additional capacity. Resume reserves capacity for a cancelled job; a completed
job cannot resume. Unknown delivery outcomes require external reconciliation: the provider
cannot deduplicate or query. Timeout is never proof of success or failure; do not retry an
unknown delivery. A known-before-effect rejection can retry. status optionally accepts
state, scoped to the authenticated tenant; omitting state preserves previous listing.

```recordbatch
"""
        + json.dumps({"steps": steps}, indent=2)
        + "\n```\n"
    )


def materialize(destination: Path, case: Case, control: str = "starter", phase: int = 1) -> None:
    """Stage one project without grader, controls, rubrics, or toolkit repository files."""
    if control not in {"starter", "reference", "wrong"}:
        raise ValueError("unknown control")
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("recordbatch.py", "build.py", "README.md"):
        shutil.copy2(ROOT / "recordbatch" / name, destination / name)
    source = (destination / "recordbatch.py").read_text()
    if phase == 2:
        if case.id != "design-hard":
            raise ValueError("only design-hard has a second phase")
        if control == "reference":
            source = sequel_reference(source)
    elif control in {"starter", "wrong"}:
        source = defect(source, case.id)
    (destination / "recordbatch.py").write_text(source)
    (destination / "TASK.md").write_text(SEQUEL if phase == 2 else case.task)
    if control in {"reference", "wrong"}:
        readme = reference_readme(case.id)
        if control == "wrong" and case.family == "docs":
            readme = readme.replace('"ok": true', '"ok": false', 1)
        (destination / "README.md").write_text(readme)
