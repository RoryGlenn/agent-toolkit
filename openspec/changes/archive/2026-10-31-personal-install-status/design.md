# Design

## Context

See proposal.md for motivation. `plan_install` currently combines canonical selection with migration and conflict checks. `linked_to` accepts role symlinks for historical restore semantics. Status must not reuse migration plans or broaden that helper's meaning.

## Goals / Non-Goals

**Goals:** Share canonical selection, retain install/restore behavior, and check linkage without writes.

**Non-Goals:** Receipt ownership inference, repair, legacy migration inspection, live-host verification, or content freshness claims.

## Decisions

- Extract only skill selection from `plan_install`; reuse its inventory, alias warning and dependency resolver. Suppress bytecode generation during the status-only lazy import. Reusing install plans would conflate conflicts and legacy retirements with expected destinations.
- Build sorted unique expected skills and roles. Use lstat for presence and type; skills must have the installer's exact canonical absolute source target, roles must be regular files with the source device/inode. Equivalent relative symlinks remain different, per the clarified trial contract. Equal bytes are insufficient; do not change restore's existing helper.
- Require explicit `--home` for status as specified. Reuse CLI root resolution and honor `--codex-home`; no destination or receipt directories are created or read as authority.
- Emit one JSON object for completed inspection and inspection/selection/argument errors. Argument errors retain stderr diagnostics with nonzero exit. Entry keys are area, name and state; top-level errors include an error string and empty entries.
- Reject invalid source trees and unsafe destination parent layouts using existing read-only checks. Such failures are invalid inspection rather than fabricated destination states.

## Risks / Trade-offs

- Concurrent filesystem changes → report only an inspection-time observation; errors return nonzero, with no repair.
- Hardlink bytes can change in place → current means current linkage, not evidence of pristine shipped content or ownership.
- Reading metadata can update filesystem access times → non-mutation tests compare entries, inode, mode, modification time, link targets and bytes, excluding access times.

## Migration Plan

No migration is needed. Existing install and restore remain available unchanged; removing the status command rolls back this feature without modifying host data.
