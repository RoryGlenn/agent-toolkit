# Tasks

## 1. Personal status

- [x] 1.1 Implement canonical read-only status selection, linkage classification, CLI output and exit behavior; add focused installer behavior/non-mutation tests and README examples and limits, verified by installer tests.

## 2. Integration checks

- [x] 2.1 Run the full unittest suite, Ruff lint/format, mypy, authoring check, installer check, diff whitespace and strict OpenSpec validation; record exact results and remaining limits for independent parent review.

## Independent review and integration

The parent completed independent review and source-bound behavior verification.
The final integrated implementation passes all 35 behavior probes, 60 installer
tests, and 29 project-bootstrap tests. Full discovery ran 226 tests with 224
passing and the same two baseline socket-permission errors; full-suite success
remains unavailable on this host. Static, authoring, package, and strict OpenSpec
checks passed. Final review and verification records are under
`experiments/openspec-pilot/evidence/` (paths from repository root). Per-feature
writer counts above describe the original prototype, not the integrated state.
