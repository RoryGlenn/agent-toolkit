# PR #19 integration verification — 13 November 2026

Status: prepared locally, with a pending merge. This record does not establish a
commit, push, hosted CI run, or merge of the PR.

## Source and changes

- Published pilot head: `489e3e7162a70870be7d60c1cb417cb349c03f9a`.
- Integrated main: `68ea80d5decb7df8f4cccb59f1e7f2df53e579ec`.
- Main's README organization and optional legacy-code capability are preserved.
- Pilot catalog, personal-status, project-integrity, and opt-in OpenSpec guidance remain documented.
- The status-all test now verifies actual expected role names instead of assuming six roles;
  main supplies seven. CLI behavior did not require a repair.
- Frozen pilot evidence and all seven recorded generated-file fingerprints are unchanged.

An independent source reviewer found no actionable issue in integration or the test
correction. The reviewed tracked integration diff, before adding this record and the
maintenance change files, has SHA-256
`5758a76820e374e2a903072dd08479fbf12ead6d4284b1a8d92ebeffafb57b10`.

## Verification

Environment: Ubuntu Linux x86_64, Python 3.12.3, uv 0.10.2, OpenSpec 1.16.0.

| Check | Observed result |
| --- | --- |
| Installer tests | 60 passed |
| Project bootstrap tests | 29 passed |
| Full unit discovery | 254 run, 252 passed, two environment errors, no failures |
| Original feature probes on the integrated source | 35/35 passed |
| Existing trusted benchmark control phases | 13/13 passed |
| Ruff lint/format, mypy including strict evaluator typing | Passed |
| Authoring, upstream identity, package, whitespace checks | Passed |
| Strict current/change and archived OpenSpec validation | Passed |

The catalog probe's expected inventory and human output use main `68ea80d`, which
includes the newer capability. This is fresh integration verification; no frozen
comparison result or original baseline was rewritten. Additional isolated CLI checks
verified legacy-code catalog/selection, personal install and current/missing-role status,
project bootstrap/integrity, and edited-owned-file rejection. Status and integrity checks
preserved their inputs.

The two unit errors occurred before native assertions, at Bubblewrap loopback setup:
`Failed RTM_NEWADDR: Operation not permitted`. The original baseline reproduced these
errors during the preceding review. They establish neither a new regression nor successful
native isolation. Hosted checks must run against the delivered integration.

Commands used include `uv sync --locked --group dev`, locked unittest discovery,
Ruff checks, mypy, `authoring.py check`, `skill_authoring verify-upstream`, `install.py check`,
`python -m benchmarks validate`, and strict current/archived OpenSpec validation.
Detailed receipts and snapshots are retained in the task-owned local verification directory.

## Delivery boundary

The local integration has no unresolved Git paths. Commit, push, hosted CI, and final
remote readback remain separate steps. The broader OpenSpec adoption issue is unchanged.
