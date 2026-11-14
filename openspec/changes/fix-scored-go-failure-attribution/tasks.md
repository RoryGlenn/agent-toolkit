# Tasks

## 1. Integration

- [x] 1.1 Resolve the CI conflict while preserving both locked checks and opt-in qualification; verify no unmerged paths remain.

## 2. Failure attribution

- [x] 2.1 Add scored/control assertion and race regressions plus incomplete-execution counterexamples; demonstrate the new regressions fail before the repair.
- [x] 2.2 Pass scored context through the evaluator, correct result attribution, and document the distinction; verify targeted tests and final objective grades.
- [x] 2.3 Deduplicate identical system runtime mounts when Python's base prefix is `/usr`; add a failing regression and rerun real runtime qualification.

## 3. Validation and qualification

- [x] 3.1 Run required repository checks and independent review/verification; record exact results and unavailable checks.
- [ ] 3.2 Run existing model-free Linux runtime/resource qualification and, if prerequisites pass, all four project gates; retain failed attempts and cleanup evidence.
- [x] 3.3 Record the final source/diff identity, validation receipts, and remaining delivery or qualification blockers.

The latest runtime attempt is blocked at nested tmpfs mount (`EACCES`, exit one,
zero OOM events); cleanup completed. Native/budget and all four case gates remain
unexecuted. See `benchmarks/large_projects/verification/review-followup-2026-11-13.md`.

## Workflow follow-up

- Commit and push only with the user's separate delivery authorization, then verify hosted CI and PR state.
- Archive after all required qualification and review gates pass; preserve this active record if a gate remains unavailable.
