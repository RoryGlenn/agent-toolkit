# Proposal

## Why

Projects need to verify their installed toolkit without modifying it or comparing it to newer source. The existing bootstrap command plans updates and therefore cannot serve as a read-only integrity probe.

## What Changes

- Add `bootstrap --project PATH --check` with human-readable success and failure results.
- Verify the recorded manifest, owned file bytes, and the managed AGENTS.md block without writes or current-source validation.
- Reject check combined with update, dry-run, skill selection, all, or target.
- Document and test the read-only contract and source independence.

## Capabilities

### New Capabilities

- `project-toolkit-integrity`: Verify recorded project toolkit ownership and content without mutation.

### Modified Capabilities

None.

## Impact

`install.py`, `project_bootstrap.py`, bootstrap tests, and README. No dependencies, installation layout changes, or changes to normal bootstrap/update semantics are required.
