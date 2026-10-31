# Proposal

## Why

Personal installations need a read-only way to inspect selected capabilities before deciding whether to reinstall. Content equality alone cannot establish the intended skill symlink or Codex role hardlink.

## What Changes

- Add `install.py status` with the install target, selection, aliases, dependency closure and explicit-home rules.
- Report expected destinations as current, missing or different, in human output or a versioned JSON object.
- Preserve all source and destination entries; status never creates directories, receipts or repairs.
- Document linkage and inspection limits and test observable behavior and non-mutation.

## Capabilities

### New Capabilities

- `personal-installation-status`: Read-only linkage inspection of selected personal skills and associated Codex roles.

### Modified Capabilities

None.

## Impact

Changes are limited to `install.py`, installer tests, README guidance and this change's planning artifacts. No dependencies, host configuration or install/restore behavior changes are intended.
