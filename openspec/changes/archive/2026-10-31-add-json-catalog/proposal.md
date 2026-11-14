# Proposal

## Why

Scripts need a stable catalog without parsing human-oriented prose. An opt-in JSON form can expose the existing validated inventory and associations while preserving the current list command.

## What Changes

- Add `python3 install.py list --json` emitting one versioned JSON object.
- Include canonical skill names, descriptions, direct dependencies, and actual runtime role names for every supported host, with deterministic ordering.
- Preserve human output and read-only operation; document usage and test the contract.

## Capabilities

### New Capabilities

- `package-catalog`: Read-only human and machine-readable discovery of packaged skills and associated roles.

### Modified Capabilities

None.

## Impact

`install.py`, installer behavior tests, and README usage. Reuse the existing inventory, `AGENTS` associations, TOML role metadata, and `project_bootstrap.SKILL_DEPENDENCIES`; add no dependencies or installation side effects.
