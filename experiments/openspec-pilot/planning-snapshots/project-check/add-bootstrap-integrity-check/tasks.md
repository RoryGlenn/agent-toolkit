# Tasks

## 1. Integrity mode

- [x] 1.1 Implement recorded manifest and managed-content verification, exclusive CLI mode, README guidance, and subprocess non-mutation/drift/source-independence regressions; verify focused bootstrap tests pass.

## 2. Integration checks

- [x] 2.1 Run the full required repository unit, lint, format, type, authoring, installer, whitespace, and OpenSpec validation checks; report exact results and limitations.

## Workflow follow-up

- Parent performs independent review and verification against the complete diff.
- Do not archive before that review.

## Writer verification results

- Focused bootstrap suite: 29 tests passed.
- Full unit discovery: 211 tests run, 209 passed, two environment errors. Both native benchmark preflight cases fail at `socket.socket()` with `PermissionError: [Errno 1] Operation not permitted`; no benchmark source was changed.
- Ruff lint and formatting, mypy (22 source files), authoring structure, package catalog, whitespace, and strict OpenSpec validation passed.
- Existing development environment was used without dependency installation. Parent review and independent verification remain pending.
