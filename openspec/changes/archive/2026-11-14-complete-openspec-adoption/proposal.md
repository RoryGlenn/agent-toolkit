# Proposal

## Why

Issue [#18](https://github.com/RoryGlenn/agent-toolkit/issues/18) requires a substantial OpenSpec exercise and demonstrated removal of duplicate planning guidance before deciding whether to continue adoption. Project bootstrap currently conflates requested capabilities with dependencies and rejects deliberate selection changes, preventing safe retirement of obsolete packages.

## What Changes

- Exercise [#16 phase 1](https://github.com/RoryGlenn/agent-toolkit/issues/16) with explicit, previewable project reconfiguration and retirement, using the existing ownership checks and rollback transaction.
- Write v2 manifests with requested roots separate from their dependency closure. Continue reading and updating v1 without guessing the user's original choices; migration requires an explicit complete selection.
- Validate historical ownership independently of the current catalog, so an absent package can be inspected and deliberately retired.
- Shorten the existing implementation skill: let upstream own planning, task tracking, synchronization, and archive for opted-in substantial work; keep one writer, independent review, real tests, authorization, and ordinary-project fallback.
- Evaluate substantial work, ordinary projects, trivial work, conflicting requirements, missing tooling, and upstream/toolkit coexistence. Record measured source changes, failures, handoffs, and remaining maintenance costs before recommending whether to continue.

## Capabilities

### New Capabilities

- `project-toolkit-reconfiguration`: explicit capability/host changes, versioned selection migration, historical ownership and safe retirement.
- `engineering-change-workflow`: opt-in upstream planning with one maintained task record and retained engineering evidence and authorization.

### Modified Capabilities

- `project-toolkit-integrity`: recognize both manifest versions and reject the new mutation flag with check mode.

## Impact

`install.py`, `project_bootstrap.py`, bootstrap tests, the implementation workflow skill and its review/evaluation records, contributor/user documentation, and OpenSpec records. No new runtime dependency, wrapper skill, router, agent format, default selection change, personal installation changes, or automatic OpenSpec installation. No catalog package is removed. Other #16 phases, remote publication, and issue closure are separate from this local change. Preserve frozen pilot evidence and unrelated active changes.
