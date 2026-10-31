# Tasks

## 1. Integrity mode

- [x] 1.1 Implement recorded manifest and managed-content verification, exclusive CLI mode, README guidance, and subprocess non-mutation/drift/source-independence regressions; verify focused bootstrap tests pass.

## 2. Integration checks

- [x] 2.1 Run the full required repository unit, lint, format, type, authoring, installer, whitespace, and OpenSpec validation checks; report exact results and limitations.

## Independent review and integration

The parent completed independent review and source-bound behavior verification.
The final integrated implementation passes all 35 behavior probes, 60 installer
tests, and 29 project-bootstrap tests. Full discovery ran 226 tests with 224
passing and the same two baseline socket-permission errors; full-suite success
remains unavailable on this host. Static, authoring, package, and strict OpenSpec
checks passed. Final review and verification records are under
`experiments/openspec-pilot/evidence/` (paths from repository root). Per-feature
writer counts above describe the original prototype, not the integrated state.
