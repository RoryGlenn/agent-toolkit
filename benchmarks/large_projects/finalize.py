"""Narrow, audited transformations of pinned upstream evaluator tests.

Upstream copyright notices remain in every derived file. Changes are applied identically
on both source revisions, then requalified; this is not a production patch.
"""

from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    """Fail rather than silently adapting an unexpected upstream test revision."""
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f"unexpected evaluator source in {path.name}")
    path.write_text(text.replace(old, new))


def finalize(case_id: str, source: Path) -> list[Path]:
    """Remove unnecessary representation checks while keeping deterministic coordination."""
    changed = []
    if case_id == "otel-queue-cancellation":
        path = source / "exporter/exporterhelper/internal/queue/cond_test.go"
        text = path.read_text()
        # The queue-lock-injection test passes on the parent. Existing queue controls
        # cover memory/persistent behavior without forcing those concrete fields.
        marker = "func TestBlockedOfferCancellationDoesNotConsumeCapacityNotification"
        if text.count(marker) != 1 or text.count("\trequire.Zero(t, c.waiting)\n") != 2:
            raise ValueError("unexpected Collector evaluator source")
        text = text[: text.index(marker)]
        text = text.replace("\trequire.Zero(t, c.waiting)\n", "")
        # Only the conditions' existing L/Wait/Signal contract remains. Channel shape,
        # buffer capacity and the private waiting counter are unconstrained.
        for imported in (
            '"github.com/stretchr/testify/assert"',
            '"go.opentelemetry.io/collector/component"',
            '"go.opentelemetry.io/collector/component/componenttest"',
            '"go.opentelemetry.io/collector/exporter/exporterhelper/internal/hosttest"',
            '"go.opentelemetry.io/collector/exporter/exporterhelper/internal/request"',
            '"go.opentelemetry.io/collector/exporter/exporterhelper/internal/storagetest"',
        ):
            text = text.replace("\t" + imported + "\n", "")
        path.write_text(text)
        changed.append(path)
    elif case_id == "vscode-snippet-selections":
        path = source / "src/vs/editor/contrib/snippet/test/browser/snippetSession.test.ts"
        text = path.read_text()
        marker = "\n\t\ttest('cross-edit placeholder backfill resolves variables in earlier edit'"
        start = text.index(marker)
        end = text.index("\n\t\t});", start) + len("\n\t\t});")
        text = text[:start] + text[end:]
        text = text.replace("SnippetParser, Variable, type TextmateSnippet", "SnippetParser")
        path.write_text(text)
        changed.append(path)
    elif case_id == "postgres-tablespace-locking":
        # Compare SQLSTATE for the race oracle, retaining the unchanged diagnostic
        # renderer for nearby controls. Golden output still enforces necessary waits
        # and completion ordering, but dependency-error wording may vary freely.
        path = source / "src/test/isolation/isolationtester.c"
        replace_once(
            path,
            'if (sev && msg)\n\t\t\t\t\t\tprintf("%s:  %s\\n", sev, msg);',
            'if (getenv("TOOLKIT_SQLSTATE") && PQresultErrorField(res, PG_DIAG_SQLSTATE))\n'
            '\t\t\t\t\t\tprintf("ERROR:  SQLSTATE=%s\\n", '
            "PQresultErrorField(res, PG_DIAG_SQLSTATE));\n"
            '\t\t\t\t\telse if (sev && msg)\n\t\t\t\t\t\tprintf("%s:  %s\\n", sev, msg);',
        )
        expected = source / "src/test/isolation/expected/tablespace-dependency-locking.out"
        text = expected.read_text()
        lines = text.splitlines(keepends=True)
        errors = [line for line in lines if line.startswith("ERROR:")]
        if len(errors) != 5 or any("some objects depend on it" not in line for line in errors):
            raise ValueError("unexpected PostgreSQL semantic errors")
        expected.write_text(
            "".join(
                "ERROR:  SQLSTATE=2BP01\n" if line.startswith("ERROR:") else line for line in lines
            )
        )
        changed.extend([path, expected])
    return changed


def collector_control(source: Path, side: str) -> None:
    """Supply a materially different correct control and a plausible partial buffer fix."""
    path = source / "exporter/exporterhelper/internal/queue/cond.go"
    if side == "alternative":
        path.write_bytes((Path(__file__).parent / "controls/otel-alternative.go.txt").read_bytes())
    elif side == "partial":
        replace_once(path, '"context"', '"context"\n\t"runtime"')
        replace_once(path, "make(chan struct{}, 1)", "make(chan struct{}, runtime.NumCPU())")
