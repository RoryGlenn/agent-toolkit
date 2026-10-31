# Tasks

## 1. Catalog output

- [x] 1.1 Add list-local JSON output using validated inventory and shared dependencies, document its schema, and add behavior tests for exact output, ordering, direct dependencies, runtime roles, invalid packages, and read-only operation; verify installer tests and the documented CLI command pass.

## 2. Integration checks

- [x] 2.1 Run unittest discovery, Ruff lint/format checks, mypy, authoring validation, installer check, diff whitespace check, and strict OpenSpec validation; report exact results and any unavailable checks.

Verification: installer tests pass (50 tests); full discovery ran 208 tests with 206 passing and two errors in existing native benchmark preflight tests because this sandbox denies `socket.socket()` creation (`PermissionError: [Errno 1]`). Full-suite success remains unverified in an environment permitting those sockets. Ruff lint/format, mypy (22 files), authoring structure, installer package validation, diff whitespace, and strict OpenSpec validation pass. Human catalog output matches the pre-change version byte for byte (4,999 bytes).

## Workflow follow-up

- Parent independently reviews and verifies the complete uncommitted diff before freezing.
- Keep the change unarchived until that review completes.
