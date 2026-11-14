# Design

## Context

See proposal.md for the goal and accepted issue boundaries. Baseline `f24fc4193911768f0b0fe3dea2df50ea642d6295` has a sound file transaction: `collect_files`, the old/new path union preflight, and `apply_changes` with a last-written manifest. `validate_manifest` optionally couples old skill names to the live inventory; v1 stores only the resolved closure. The current workflow skill repeats planning/handoff/completion lists even where OpenSpec owns the change lifecycle.

## Goals / Non-Goals

Keep the existing transaction and source provenance format. Add one explicit mode and one versioned manifest field rather than a second installer or lifecycle framework. No personal synchronization, automatic dependency installation, named-role changes, catalog removal or broader default adoption.

## Decisions

- Add `--reconfigure`, mutually exclusive with `--update`, requiring an existing record and an explicit skill or host choice. Reuse the complete preview and transaction. Making selection flags silently destructive during update was rejected because a familiar update could retire capabilities.
- New records use `agent-toolkit-project/v2`, `requested_skills` and the existing resolved `skills`. New roots are canonical sorted names; closure remains computed by the existing resolver. V2 host-only changes reuse recorded roots. A single optional/null roots field was rejected because it obscures legacy ambiguity.
- V1 ordinary repeat/update remains v1 and conservatively treats all recorded skills as retained. A v1 reconfiguration requires a complete explicit root list; never guess that routing or a shared skill was only a dependency. An unavailable retained root fails with a reconfiguration hint.
- Historical manifest validation accepts safe recorded canonical skill names, independent of current availability. Only desired selection uses today's catalog. Preflight checks ALL old files and block hashes before any writes, including files about to be removed. Shared roles/dependencies follow the desired closure, not per-skill deletion.
- Keep current `source` identity and content hashes. Old record bytes authorize preflight and ordinary-error rollback; the new manifest describes the new snapshot. Project Git preserves prior ownership/provenance, so instructions require saving the old record before migration. Do not add a growing embedded history.
- Keep upstream-generated skills byte-for-byte and outside the toolkit catalog. Condense the existing implementation skill around its engineering responsibility and a conditional upstream handoff. One `tasks.md` owns progress; validation reports own receipts, not duplicate task lists. Keep the ordinary path self-contained and available offline without OpenSpec.

## Risks / Trade-offs

- Concurrent edits and process crashes exceed an in-memory transaction's guarantees → preserve existing compare-before-write/rollback checks, document interruption limits and use project Git for recovery; do not promise crash atomicity.
- Dependencies can change in new sources → explicit update accepts newly required dependencies; unexplained removal or selection changes require reconfiguration. Check dependency retention and shared roles with behavior tests.
- Shorter instructions could omit needed handoff checks → independent review and five concrete adoption cases assess retained authority, real tests, role independence and missing-tool disclosure.
- A one-off exercise adds more lifecycle code and project records than it removes in instructions → report these categories separately; no general maintenance-saving claim or default change.

## Migration Plan

Save the project diff and old manifest in Git. Preview `bootstrap --reconfigure --skill ... --target ... --dry-run`, supplying ALL desired roots for a legacy project. Resolve edited/missing owned content or collisions; never force overwrite. Apply the reviewed selection, inspect the diff and run `bootstrap --check`. Save the new manifest and generated files with the project. Restore the prior project revision to roll back a completed migration. Ordinary failures restore prior content in-process; interruptions require inspection. No personal installation is changed by this work.
