# PR #19 integration verification — 13 November 2026

This is the initial local verification checkpoint, before commit or publication.
Later integration and delivery checkpoints are recorded below.

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

## Integration with newer main before publication

The reviewed initial tree was preserved in DCO-signed-off commit
`efbfd9dc71645bcbe27a18f8a34e0700069f1b28`. Main then advanced to
`72ef2cdc7f82e860fb9f970e6d49dc022f8f1d16`; its matched benchmark work integrated
cleanly. The pilot CLI implementation, generated workflows, and frozen evidence are unchanged.
Independent source review found no actionable issue.

Independent verification of this newer integration recorded 268 unit tests: 266 passed
and the same two Bubblewrap environment errors, with no assertion failures. Installer
60/60, bootstrap 29/29, and the original feature probes 35/35 passed. Feature expectations
use the matching main `72ef2cd` inventory. All seven generated hashes still match and frozen
pilot evidence has zero changed bytes.

All 13 existing benchmark phases and seven matched controls passed. Demo controls
preserved rollback row counts 0/1/0, and CLI demo staging produced matching diffs/prompts
without actors. Lint, formatting, typing, authoring/upstream/package, whitespace, and
strict OpenSpec checks passed. Hosted publication and CI are distinct from these local results.

## Published code checkpoint

DCO-signed-off code commit `70886442d014d8006b26cb34d0ba75d5c7cc3541` was pushed to
the existing PR #19 branch. Its [push CI](https://github.com/RoryGlenn/agent-toolkit/actions/runs/43547834843)
and [pull-request CI](https://github.com/RoryGlenn/agent-toolkit/actions/runs/43547839650)
both passed Python 3.11 and 3.13 checks. The remote branch includes main `72ef2cd`,
and the PR remains open as a draft. No merge was performed. This delivery receipt is
a documentation-only follow-up to that tested code checkpoint.
