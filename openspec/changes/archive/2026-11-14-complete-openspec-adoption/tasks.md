# Tasks

## 1. Safe selection and migration

- [x] 1.1 Add structurally validated v1/v2 ownership records with separate v2 requested roots; verify invalid-record tests and unchanged legacy repeat/update behavior.
- [x] 1.2 Add explicit reconfiguration using the existing preflight and transaction; verify real CLI selection/host changes, obsolete-package retirement, shared dependency retention and invalid-mode refusal.
- [x] 1.3 Cover dry runs, edited/missing/unmanaged/link refusal, upstream-file coexistence and late-failure rollback after additions/removals; verify regression controls fail against the baseline.
- [x] 1.4 Document executable migration, preview, check and recovery commands in README and run them against a disposable project.

## 2. Upstream ownership and simpler guidance

- [x] 2.1 Condense the existing implementation skill around upstream planning and retained engineering responsibilities; verify five adoption cases and ordinary selective installation without OpenSpec.
- [x] 2.2 Record the responsibility map, exact simplifications, source measurements, handoffs, rework and upgrade obligations; review the evidence before updating affected authoring fingerprints.

## 3. Independent acceptance

- [x] 3.1 Have separate read-only agents review the complete diff and verify the original requirement through actual CLI behavior and required gates; resolve findings and recheck changed bytes.
- [x] 3.2 Run full unit, lint, formatting, typing, authoring, package/upstream, benchmark and strict OpenSpec checks; pass available gates, compare pre-existing environment failures with baseline, and record exact identities, results, limits and local delivery status.

## Workflow follow-up

- After all tracked tasks pass, synchronize the three capability deltas and archive this change using upstream OpenSpec; validate the resulting main specs and archive and preserve unrelated active changes.
- Keep this one implementation checklist. Review/verification reports contain evidence and dispositions, not parallel progress checklists.
- Prepare issue/PR text for review. Commit, push, PR creation, issue edits/closure and merge require their distinct user permissions; the current request authorizes local completion only.
