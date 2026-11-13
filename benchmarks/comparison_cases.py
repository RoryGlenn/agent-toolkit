"""Matched campaign fixtures and curator checks."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks.cases import CASES, get_case, materialize
from benchmarks.files import hashes, snapshot
from benchmarks.oracles import Grade
from benchmarks.process import Executor, TrustedControlExecutor
from benchmarks.runtime import fingerprint

REVIEW_PROMPT = "Review this diff."
LEDGER = """from sqlite3 import Connection


def ensure_ledger(db: Connection) -> None:
    \"\"\"Create the ledger table and index on the caller's connection.\"\"\"
    db.execute("CREATE TABLE IF NOT EXISTS ledger (amount INTEGER NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS ledger_amount ON ledger (amount)")
"""
LEDGER_CLEAN = LEDGER.replace(
    '    db.execute("CREATE INDEX IF NOT EXISTS ledger_amount ON ledger (amount)")',
    '    db.execute(\n        "CREATE INDEX IF NOT EXISTS ledger_amount ON ledger (amount)"\n    )',
)
LEDGER_SEEDED = (
    LEDGER[: LEDGER.index("    db.execute(")]
    + '''    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS ledger (amount INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS ledger_amount ON ledger (amount);
        """
    )
'''
)
ROLLBACK_CHECK = """
import json
import sqlite3
from ledger import ensure_ledger

options = {}
if hasattr(sqlite3, "LEGACY_TRANSACTION_CONTROL"):
    options["autocommit"] = sqlite3.LEGACY_TRANSACTION_CONTROL
with sqlite3.connect(":memory:", **options) as db:
    ensure_ledger(db)
    index = db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ledger'"
    ).fetchone()
    db.execute("INSERT INTO ledger VALUES (42)")
    ensure_ledger(db)
    db.rollback()
    rows = db.execute("SELECT count(*) FROM ledger").fetchone()[0]
    print(json.dumps({"startup": index == ("ledger_amount",), "rows_after_rollback": rows}))
"""
LEGACY = '''"""Daily totals before posting to the external accounting client."""

from collections.abc import Callable, Iterable


def post_total(rows: Iterable[int], post: Callable[[str, int], None]) -> int:
    """Post the sum through an injected accounting client and return the amount."""
    total = sum(rows)
    post("daily-total", total)
    return total
'''
ROUTINE = 'LABEL = "Pending jobs"\n'
READY = 'print("READY")\n'
LEGACY_POST_REFERENCE = LEGACY.replace(
    "    total = sum(rows)",
    "    iterator = iter(rows)\n"
    "    try:\n"
    "        first = next(iterator)\n"
    "    except StopIteration:\n"
    "        return 0\n"
    "    total = first + sum(iterator)",
)
LEGACY_TOTAL_REFERENCE = LEGACY.replace(
    "    total = sum(rows)",
    "    total = 0\n"
    "    for row in rows:\n"
    "        if row < 0:\n"
    "            raise ValueError('negative row')\n"
    "        total += row",
)


@dataclass(frozen=True)
class ComparisonCase:
    """The frozen prompt, baseline, product inputs and scoring contract."""

    id: str
    family: str
    prompt: str
    files: dict[str, bytes]
    original: dict[str, bytes]
    rubric: tuple[str, ...] = ()
    read_only: bool = False

    def identity(self) -> dict[str, Any]:
        """Include the exact actor and grader inputs in the campaign identity."""
        details = {
            "case_id": self.id,
            "family": self.family,
            "prompt_fingerprint": fingerprint(self.prompt),
            "product_hashes": hashes(self.files),
            "original_hashes": hashes(self.original),
            "read_only": self.read_only,
            "rubric": list(self.rubric),
        }
        return {**details, "case_fingerprint": fingerprint(details)}


RECORD_CASES = {case.id for case in CASES}
DEMO_CASES = ("rollback-seeded", "rollback-clean")
FULL_CASES = ("integrated-easy", "ddia-medium", "rollback-seeded", "routine-label")
ROLE_CASES = {
    "ddia_agent": ("ddia-skill", ("ddia-hard", "ddia-medium")),
    "documentation_agent": ("documentation-skill", ("docs-easy", "docs-hard")),
    "software_design_agent": ("software-design-skill", ("design-medium", "design-easy")),
    "legacy_code_agent": ("legacy-code-skill", ("legacy-post", "legacy-total")),
    "implementation_owner_agent": (
        "issue-to-tested-pr-skill",
        ("integrated-easy", "integrated-medium"),
    ),
    "adversarial_reviewer_agent": ("independent-diff-review-skill", DEMO_CASES),
    "verifier_agent": ("independent-diff-review-skill", ("release-broken", "release-clean")),
}
EXTRA_CASES = {
    *DEMO_CASES,
    "legacy-post",
    "legacy-total",
    "routine-label",
    "release-clean",
    "release-broken",
}


def archive_fixture(broken: bool) -> bytes:
    """Build a byte-stable Python release artifact with a known startup contract."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(zipfile.ZipInfo("__main__.py"), "from app import main\nmain()\n")
        if not broken:
            archive.writestr(zipfile.ZipInfo("app.py"), "def main():\n    " + READY)
    return stream.getvalue()


def comparison_case(case_id: str) -> ComparisonCase:
    """Load the same actor-facing materials in all arms."""
    if case_id in RECORD_CASES:
        case = get_case(case_id)
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            materialize(workspace, case)
            files = snapshot(workspace)
        return ComparisonCase(case_id, "recordbatch", case.task, files, files, case.review)

    if case_id in DEMO_CASES:
        seeded = case_id == "rollback-seeded"
        files = {"ledger.py": (LEDGER_SEEDED if seeded else LEDGER_CLEAN).encode()}
        target = (
            "Report the changed call, the caller's pending transaction, and the row "
            "that survives rollback. Propose preserving the caller's transaction."
            if seeded
            else "Recognize that the formatting change preserves the separate calls and rollback."
        )
        return ComparisonCase(
            case_id,
            "ledger",
            REVIEW_PROMPT,
            files,
            {"ledger.py": LEDGER.encode()},
            (target, "Report only material findings supported by the changed code or a check."),
            read_only=True,
        )

    if case_id in {"release-broken", "release-clean"}:
        broken = case_id == "release-broken"
        files = {"release.pyz": archive_fixture(broken)}
        expected = (
            "Identify the exact artifact, failed startup, and missing app module. Reject release."
            if broken
            else "Identify the exact artifact, evidence it prints READY, and a passing verdict."
        )
        prompt = (
            "Verify release.pyz for shipment. It must run by itself with Python and print READY. "
            "Report the artifact SHA-256, the command and result, and the release verdict."
        )
        return ComparisonCase(
            case_id,
            "release",
            prompt,
            files,
            files,
            (expected, "Base the verdict on actual execution of the supplied artifact."),
            read_only=True,
        )

    if case_id in {"legacy-post", "legacy-total"}:
        requirement = (
            "An empty batch should return 0 without posting. A nonempty batch posts once, even "
            "when its total is zero."
            if case_id == "legacy-post"
            else "Reject a negative row with ValueError before posting. Accept zero and preserve "
            "posting for a nonempty valid batch."
        )
        prompt = (
            f"Update post_total in invoice.py. {requirement} Preserve one-shot iterables, the "
            "daily-total key, and callback failures. Add a focused regression test."
        )
        files = {"invoice.py": LEGACY.encode()}
        return ComparisonCase(case_id, "legacy", prompt, files, files)

    if case_id == "routine-label":
        files = {"labels.py": ROUTINE.encode()}
        return ComparisonCase(
            case_id, "routine", "Rename the display label to Queued jobs.", files, files
        )
    raise ValueError(f"unknown matched case: {case_id}")


def grade_fixture(case: ComparisonCase, workspace: Path, executor: Executor) -> Grade:
    """Verify fixed fixtures and score submitted non-RecordBatch changes."""
    grade = Grade(case.id, 1, needs_review=list(case.rubric))
    python = str(Path(sys.executable).resolve())
    expected: dict[str, int] | bool
    if case.family == "ledger":
        source = ROLLBACK_CHECK
        expected = {"startup": True, "rows_after_rollback": int(case.id == "rollback-seeded")}
    elif case.family == "release":
        result = executor.execute([python, "release.pyz"], workspace)
        grade.commands.append(result.to_dict())
        broken = case.id == "release-broken"
        matches = (
            result.returncode == 1 and "No module named 'app'" in result.stderr
            if broken
            else result.returncode == 0 and result.stdout == "READY\n"
        )
        return finish_grade(grade, matches, "exact archive startup outcome")
    elif case.family == "legacy":
        special = (
            "assert post_total(iter(()), post) == 0 and seen == []\n"
            if case.id == "legacy-post"
            else "try:\n    post_total(iter((2, -1)), post)\nexcept ValueError:\n    pass\n"
            "else:\n    raise AssertionError('negative row accepted')\nassert not seen\n"
        )
        source = (
            "from invoice import post_total\nseen = []\ndef post(*args): seen.append(args)\n"
            + special
            + "assert post_total(iter((0, 0)), post) == 0\n"
            "assert post_total(iter((1, 2)), post) == 3\n"
            "assert seen == [('daily-total', 0), ('daily-total', 3)]\n"
            "def fail(*args): raise RuntimeError('offline')\n"
            "try:\n    post_total(iter((2,)), fail)\nexcept RuntimeError:\n    pass\n"
            "else:\n    raise AssertionError('missing callback failure')\nprint('true')\n"
        )
        expected = True
    else:
        expected_label = ROUTINE.replace("Pending", "Queued")
        source = (
            "from pathlib import Path\nimport json\n"
            f'print(json.dumps(Path("labels.py").read_text() == {expected_label!r}))'
        )
        expected = True
    result = executor.execute([python, "-B", "-c", source], workspace)
    grade.commands.append(result.to_dict())
    try:
        matches = result.returncode == 0 and json.loads(result.stdout) == expected
    except (TypeError, ValueError):
        matches = False
    return finish_grade(grade, matches, f"{case.id} behavior control")


def finish_grade(grade: Grade, matches: bool, check: str) -> Grade:
    """Preserve fixture failures and leave judgment pending."""
    grade.objective_complete = matches
    grade.checks.append(check)
    if not matches:
        grade.failures.append(check)
        grade.status = "failed"
    else:
        grade.status = "needs_review" if grade.needs_review else "passed"
    return grade


def demo_controls() -> dict[str, dict[str, Any]]:
    """Execute only repository-owned ledger controls and return observed row counts."""
    out = {}
    for label, code, expected in (
        ("original", LEDGER, 0),
        ("seeded", LEDGER_SEEDED, 1),
        ("clean", LEDGER_CLEAN, 0),
    ):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "ledger.py").write_text(code)
            result = TrustedControlExecutor().execute(
                [sys.executable, "-B", "-c", ROLLBACK_CHECK], workspace
            )
            if result.returncode != 0:
                raise ValueError(f"ledger control {label} failed: {result.stderr}")
            actual = json.loads(result.stdout)
            if actual != {"startup": True, "rows_after_rollback": expected}:
                raise ValueError(f"unexpected ledger outcome for {label}: {actual}")
            out[label] = actual
    return out


def comparison_controls() -> list[dict[str, Any]]:
    """Qualify the additional repository-owned fixture oracles without model access."""
    demo_controls()
    controls = []
    for case_id in sorted(EXTRA_CASES):
        case = comparison_case(case_id)
        reference = case.files
        if case.family == "ledger":
            wrong = comparison_case(
                "rollback-clean" if case_id == "rollback-seeded" else "rollback-seeded"
            ).files
        elif case.family == "release":
            wrong = {"release.pyz": archive_fixture(case_id == "release-clean")}
        elif case.family == "routine":
            wrong = case.files
            reference = {"labels.py": ROUTINE.replace("Pending", "Queued").encode()}
        else:
            wrong = case.files
            source = LEGACY_POST_REFERENCE if case_id == "legacy-post" else LEGACY_TOTAL_REFERENCE
            reference = {"invoice.py": source.encode()}
        outcomes = {}
        for label, files in (("reference", reference), ("wrong", wrong)):
            with tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                for name, data in files.items():
                    (workspace / name).write_bytes(data)
                outcomes[label] = grade_fixture(case, workspace, TrustedControlExecutor())
        accepted, rejected = outcomes["reference"], outcomes["wrong"]
        controls.append(
            {
                "case_id": case_id,
                "validated": accepted.objective_complete
                and not accepted.failures
                and bool(rejected.failures)
                and not rejected.harness_error,
            }
        )
    return controls
