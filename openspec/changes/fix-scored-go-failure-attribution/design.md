# Design

## Context

The evaluator already distinguishes scored artifacts from trusted parent/reference
controls for compiler failure attribution. Test parsing currently loses that context.

## Decisions

- Pass the same explicit scored-artifact context into test-result parsing; default to strict control behavior.
- Require complete terminal Go outcomes, an ordinary test-failure exit, and no timeout/output truncation before attributing assertion or race failures to a candidate.
- Preserve the existing trusted negative-control treatment of unexpected races. A race must not qualify a parent merely because failure was expected.
- Reuse the existing report schema: candidate failures contain failure names and objective false; environment failures retain harness-error/unknown results.
- Resolve the workflow conflict by retaining main's locked checks and unchanged-source gate plus the branch's opt-in qualification job.
- The first local qualification exposed a duplicate `/usr` mount: system Python's base prefix
  equals an existing runtime mount. Deduplicate identical source/destination pairs while
  preserving mount ordering and all distinct read-only grants; do not change host policy.

## Risks / Trade-offs

- Reclassifying incomplete output could hide runtime faults: add missing-terminal, skip, timeout, and signal counterexamples.
- Parser tests alone do not prove evaluator wiring: verify scored/control context at the evaluator boundary and final grade behavior.
- Linux qualification may fail on host prerequisites: run existing gates without policy changes and retain actual diagnostics and cleanup evidence.
- No source, prompt, or model comparison is part of this repair.
