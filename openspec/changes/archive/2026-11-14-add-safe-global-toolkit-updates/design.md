# Design

## Context

The retained checkout is already the source of 16 global skill symlinks and seven
regular role hardlinks. It contains unpublished work. Git can replace role inodes;
restoring old bytes alone does not restore installation status. The independent
contribution scheduler owns a separate bare store and is outside this change.

## Goals / Non-Goals

The operator uses one run command and one status command. The operation owns source
identity, validation, receipts, and recovery ordering. It does not commit, stash,
publish, install dependencies, run models, or migrate source ownership silently.

## Decisions

- Retain the existing checkout and block on all tracked/untracked edits. A separate
  immutable-deployment architecture would need migration and baseline ownership but
  would still need to reconcile unpublished fixes; defer that additional lifecycle.
- Install a reviewed runtime bundle outside the checkout with explicit source/home
  configuration. Scheduled code does not self-update when public main changes.
  Its trusted installer mapping defines supported role layout; new incompatible
  catalog layouts require a reviewed runtime refresh.
- Use an exclusive advisory lock and private atomic JSON records. Fetch the public
  branch into a private ref, require ancestry, and stage a detached worktree under
  the repository root. Retain staged evidence rather than auto-delete Git worktrees.
- Run package/authoring checks, lint/format/type checks, and the installer, routing,
  project-installation and updater regression suites with the existing development
  Python. No dependency download occurs. These targeted deployment gates do not
  claim full benchmark-kernel or model-quality coverage; unavailable required gates
  block deployment.
- Validate an isolated installation and restore with the trusted installer. Before
  promotion, recheck branch, HEAD, clean state, role inodes and preserved workflow
  fingerprints. Preflight refuses destination collisions outside managed entries.
- Normal promotion is fast-forward-only. Persist a transaction first. On failure,
  restore its receipt while candidate source inodes exist, use guarded `reset --keep`
  solely to return the exact transaction to its recorded prior commit, rerun the
  preserving installer, and verify canonical linkage. Never use a hard reset.
- Detect unfinished transactions on the next run. Automatic recovery accepts only
  expected source/installation states and stops on concurrent edits. A restored
  revision's newly materialized inodes must be relinked even when bytes match.
- Configure a daily 11:30 America/New_York user timer with persistence, after the
  separate contribution job. A bounded user service runs the same manual command.
  The timer's first truthful result is blocked-local-changes until unpublished work
  is reconciled through separately authorized delivery.

## Risks / Trade-offs

- Skill switching and role refresh are not atomic across Codex processes. Use fresh
  sessions after updates; do not claim active conversations hot-reload definitions.
- Candidate code executes with the local user's authority. A separate checkout is
  filesystem isolation, not a security sandbox; only the explicitly selected public
  repository is accepted and candidate checks receive no copied credentials.
- A crash during Git mutation can leave an unusual state. Preserve the transaction
  and stop rather than force recovery through an unexpected dirty state.
- Retained candidates consume disk. Record their paths; cleanup is a separate explicit
  operation rather than broad automatic deletion.

## Migration Plan

Independent review found that expected-only inventory could omit retired entries.
Preserve a profile-bound managed-path registry across runtime refreshes and hold
catalog removals for explicit migration. Operator rollback holds the same upstream
revision until deliberate retry or a newer revision. Recovery refuses new
same-source receipts from another profile before touching them.

The second review found that matching source/profile and creation time still did
not establish receipt ownership. The installer accepts an optional safe receipt
ID and exclusively reserves its directory, recording the ID before destination
writes. The controller journals exact primary and repair IDs/paths before either
installation starts, validates their complete identity during recovery, and holds
on additional same-source receipts. It never adopts an unbound manual receipt.

Create the runtime and portable restore instructions, validate synthetic Git histories
and disposable homes, obtain independent review/verification, then enable the user
timer and inspect its real result. Keep the existing live installation unchanged
while dirty. Verify status, next timer trigger and Doc Agent preservation. Runtime
updates require rerunning setup after review; they are not silently adopted upstream.
