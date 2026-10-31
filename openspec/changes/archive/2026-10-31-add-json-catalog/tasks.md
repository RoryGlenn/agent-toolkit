# Tasks

## 1. Catalog output

- [x] 1.1 Add list-local JSON output using validated inventory and shared dependencies, document its schema, and add behavior tests for exact output, ordering, direct dependencies, runtime roles, invalid packages, and read-only operation; verify installer tests and the documented CLI command pass.

## 2. Integration checks

- [x] 2.1 Run unittest discovery, Ruff lint/format checks, mypy, authoring validation, installer check, diff whitespace check, and strict OpenSpec validation; report exact results and any unavailable checks.

Verification: installer tests pass (50 tests); full discovery ran 208 tests with 206 passing and two errors in existing native benchmark preflight tests because this sandbox denies `socket.socket()` creation (`PermissionError: [Errno 1]`). Full-suite success remains unverified in an environment permitting those sockets. Ruff lint/format, mypy (22 files), authoring structure, installer package validation, diff whitespace, and strict OpenSpec validation pass. Human catalog output matches the pre-change version byte for byte (4,999 bytes).

## Independent review and integration

The parent completed independent review and source-bound behavior verification.
The final integrated implementation passes all 35 behavior probes, 60 installer
tests, and 29 project-bootstrap tests. Full discovery ran 226 tests with 224
passing and the same two baseline socket-permission errors; full-suite success
remains unavailable on this host. Static, authoring, package, and strict OpenSpec
checks passed. Final review and verification records are under
`experiments/openspec-pilot/evidence/` (paths from repository root). Per-feature
writer counts above describe the original prototype, not the integrated state.
