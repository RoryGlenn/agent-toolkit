# Tasks

## 1. Contract and updater

- [x] 1.1 Inspect live installation, preserve a source manifest, and obtain read-only design advice; verify retained-checkout and dirty-hold decisions in design.md.
- [x] 1.2 Implement serialized preflight, public-main candidate validation and guarded promotion; verify dirty, untracked, divergent, foreign and concurrent-change regressions.
- [x] 1.3 Implement receipt-backed refresh and recovery; verify role-inode refresh, Doc Agent preservation, failed verification, interrupted transaction and repeated-run behavior.
- [x] 1.4 Document exact automated gates, holds, recovery and fresh-session limits; verify commands against disposable Git histories and homes.

## 2. Installation and schedule

- [x] 2.1 Ship fixed-runtime setup, manual commands and daily user units; verify fixture setup, path safety, idempotence and systemd syntax.
- [x] 2.2 Add portable private dotfiles restore guidance within its allowlist rules; verify referenced files and isolated setup commands.

## 3. Acceptance and workstation rollout

- [x] 3.1 Obtain independent review, verification and named documentation review of exact source bytes; resolve blockers and run required repository gates, distinguishing existing kernel limitations.
- [x] 3.2 Install reviewed runtime and enable the local timer; inspect real service result, saved configuration, next trigger, unchanged global entries and preserved Doc Agent.
- [x] 3.3 Record source identities and actual delivery limits in this task record; verify strict OpenSpec validation and final diff without committing or publishing unrelated work.

## Completion evidence

The retained source remains at `3827a69364da2c89e770eedcf19866654fff8db8`
with preserved unpublished work. Native Toolkit reviewer, verifier and documentation
agents independently accepted revision r5 after resolving retired-entry ownership,
exact receipt attribution, rollback retry policy and manual-migration guidance.
The final fourteen-file manifest and readback are private local evidence under
`~/.local/state/agent-toolkit/updates/implementation/`.

All 33 updater, 67 installer and 12 dotfiles tests passed. Full discovery recorded
397 successes and nine existing native-control errors out of 406 tests: seven
network-namespace errors, one mount-isolation error and one nested cgroup-control
error. Ruff, formatting, mypy, authoring/package checks, strict OpenSpec and systemd
validation passed. The documented candidate-validation example passed all eleven
deployment gates against a complete synthetic Git snapshot and disposable home;
that fixture did not change the live repository or publish source.

The reviewed fixed runtime, configuration and 23-entry ownership registry are saved.
The real user service exited zero with `blocked-local-changes`; all 23 expected
entries, standalone Doc Agent and global guidance remain unchanged. The daily
11:30 America/New_York timer is enabled and active; its next recorded trigger is
2026-11-15 11:30 EST. No unexpected pre-existing file changes were found.

This records completion of the local updater and its verified hold before Git
delivery. Automatic deployment was
not yet occurring: unpublished source needed reconciliation first. Project commits,
pushes, PRs and merge were not authorized at that snapshot; none had been performed.

## Authorized Git delivery

The user subsequently requested issue-to-merge delivery. The accepted scope and
remote delivery are tracked in [issue #33](https://github.com/RoryGlenn/agent-toolkit/issues/33).
Prepare the PR from the current upstream base, preserving unrelated OpenSpec edits
in their own local worktree. Reuse the unchanged reviewed implementation evidence,
verify the isolated complete patch, and require hosted CI and repository protections
before merge. Afterward, reconcile the retained source and verify its global links
and updater result against the actual merged revision.

## Workflow follow-up

- Synchronize and archive through upstream OpenSpec after independent acceptance.
- Git delivery is now authorized through issue #33. Reconcile unpublished source work before expecting automatic deployments; the enabled timer must report the hold honestly meanwhile.
