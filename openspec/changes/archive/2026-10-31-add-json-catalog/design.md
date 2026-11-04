# Design

## Context

See proposal.md for motivation. `main` validates skill and Codex TOML metadata through `inventory` before listing; human formatting lives in `print_catalog`. `project_bootstrap` owns the shared direct dependency map and validates dependency closure with `resolve_skills`.

## Goals / Non-Goals

**Goals:** Add an opt-in serialized view of the same sources and validate dependency availability before writing stdout. Preserve default output byte for byte.

**Non-Goals:** Installation status, new host formats, dependency closure in each catalog entry, and changing other command semantics.

## Decisions

- Add a list-local `--json` argument and a separate JSON formatter so existing human formatting stays untouched. Build the entire object before printing, avoiding partial JSON on validation errors.
- Read `SKILL_DEPENDENCIES` directly and validate the available inventory using `resolve_skills`; do not maintain a second map or expose expanded dependencies.
- Read runtime `name` from the role TOML files referenced by `AGENTS`. Sort skill names, direct dependencies, and role lists explicitly.
- Import dependency helpers lazily with bytecode writes disabled and restore the prior setting. A normal import could create `__pycache__`, violating read-only listing; moving the shared map is broader than this feature.

## Risks / Trade-offs

- [A separately edited package may invalidate dependencies] → fail before emitting the object and test missing dependencies.
- [Serialization tests could repeat implementation assumptions] → exercise the CLI, controlled non-sorted associations and a transitive dependency fixture, invalid inputs, escaped text, and full filesystem snapshots.
- [New code can affect unrelated commands] → retain existing human tests and run the repository gates.

## Migration Plan

Opt in with `list --json`; no migration or state changes. Roll back by removing the option and formatter. Keep this change unarchived until independent review and verification.
