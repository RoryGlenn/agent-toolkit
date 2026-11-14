# PR #6 review follow-up — 13 November 2026

This initial verification checkpoint preceded commit and publication. Linux qualification
remains **unqualified**; subsequent integration and delivery checkpoints are recorded below.

## Repairs and source

- Published PR head: `b76a30a2de7f05e733f409ef1853a2505021b9da`.
- Integrated main: `68ea80d5decb7df8f4cccb59f1e7f2df53e579ec`.
- Completed scored Go assertion/race failures now produce a failed grade and objective false.
  Unexpected races in trusted qualification controls remain unavailable; incomplete execution
  still cannot supply a score.
- Identical system mount pairs are deduplicated. On this host, Python's `/usr` base prefix
  previously duplicated the explicit `/usr` grant and prevented Docker cell creation.
- The resolved workflow retains main's locked checks and unchanged-source gate alongside
  the existing opt-in qualification job.

The evaluator-level regression reproduced a scored race being incorrectly classified as
an environment failure before repair. An independent disposable original-source check also
rejected the new attribution regressions. The duplicate-mount regression failed before
repair (nine pairs, eight unique) and passes afterward.

Independent source review found no actionable issue. The reviewed tracked integration
diff, before adding this record and maintenance change files, has SHA-256
`5d84c6620d2ab44b52856151f5b9a0af34de6fa47e4e974cae975862a10166bf`.
Implementation fingerprints:

| File | SHA-256 |
| --- | --- |
| `runner.py` | `00bf607dfdb475228fd4dbfba426750035273494e9203400221749636cda56a7` |
| `integration.py` | `03dbe3c25c72f8c90a6a19699692e184a49ff34478c21fa91e25a586ce0e5200` |
| `resources.py` | `c5b201de88b672c1ea212ad26105291d9f2a46863dc1282a0f0c7a7d33268327` |

## Local verification

Environment: Ubuntu Linux x86_64, Python 3.12.3, uv 0.10.2, OpenSpec 1.16.0.

| Check | Observed result |
| --- | --- |
| Targeted classification/pipeline tests | 33 passed |
| New attribution and mount regression methods, independent verifier | Four passed |
| Full unit discovery | 291 run, 282 passed, nine environment errors, no skips or assertion failures |
| Existing trusted benchmark control phases | 13/13 passed |
| Ruff lint/format, mypy, authoring, upstream identity, package, whitespace | Passed |
| Strict current/change and archived OpenSpec validation | Passed |

Seven unit errors occur before native assertions because Bubblewrap cannot configure
loopback (`Failed RTM_NEWADDR: Operation not permitted`). The Docker aggregate control
cannot mount nested tmpfs (`errno 13`); the sealed evaluator test cannot make `/` slave
(`Permission denied`). The Docker staging-timeout/external-cancellation test passes after
the duplicate-mount repair. These errors do not establish successful native isolation.

Routine commands use `uv sync --locked --group dev`, locked unittest discovery, Ruff,
mypy, authoring/upstream/package checks, `python -m benchmarks validate`, and strict
current/archived OpenSpec validation. Detailed receipts and before/after source snapshots
remain in the task-owned local verification directory.

## Actual runtime qualification

Both attempts used the existing `python -m benchmarks large runtime-check` CLI, the pinned
BusyBox image, and the full Codex CLI 0.165.0 package. The package archive matched the
existing release SHA-256 `f997cd6ef5987126e19cd3c82e847a4a6461270f32f97340c5e99a65fb6f9b8a`.
Each attempt used a new output directory and retained its log and command receipt.

1. The first attempt stopped at Docker creation with `Duplicate mount point: /usr`.
   It exposed the source defect repaired above. Cleanup completed.
2. The second attempt reached the nested allocated-storage control. `libc.mount(tmpfs)`
   was denied with `EACCES` (errno 13), process exit one, and zero `oom_kill` events.
   The result remained `setup_error`. Cleanup completed.

The responsible security enforcer has not been established. No host policy or container
restriction was changed, and the required exit 137 plus at least one `oom_kill` event was
not relaxed. Readback found no remaining attempt-owned containers or volumes.

Actual native-tool/descendant-budget proof and all four integrated project qualifications
were **not reached**. No source/dependency corpus was downloaded after the runtime gate
failed. No model calls or comparison study ran. A supported Linux host must still pass
the existing runtime and complete case gates before this PR qualifies; it remains a draft.

## Integration with newer main before publication

The reviewed initial tree was preserved in DCO-signed-off commit
`5a4783f7acbb7070794a3d1844d4c683bb18dc34`. Before publication, main advanced to
`72ef2cdc7f82e860fb9f970e6d49dc022f8f1d16` with matched benchmark execution.
The subsequent integration preserves both matched V1 and large-project V2 runtime
profiles, read-only workspaces, global temporary-file denial, streaming artifact reads,
large-project dispatch, frozen-delta reconciliation, and cancellation reporting.
Prompt inspection retains the execution-cell runner rather than executing on the host.

Five new integration tests cover the shared profile, prompt, artifact, cancellation,
and planning contracts. Independent source review found no actionable issue.
Independent verification of the combined source recorded:

- 310 unit tests: 301 passed, the same nine environment errors, no assertion failures or skips.
- 52/52 targeted tests, all 13 existing and seven matched benchmark control groups passed.
- Demo controls preserved rollback row counts 0/1/0; CLI staging produced matching diffs
  and prompts without starting actors.
- Lint, formatting, typing, authoring/upstream/package, whitespace, and strict OpenSpec checks passed.

A fresh runtime qualification on this combined source again stopped at nested tmpfs
mounting with `EACCES`, exit one and zero OOM events; cleanup completed. Actual
native/budget proof and all four project gates remain unexecuted. No model study ran.
The source-bound local receipts are retained in the publication verification directory.

## Published code checkpoint

DCO-signed-off code commit `0b90a72c8ece8260139f6d553660aa807afe72ea` was pushed to
the existing PR #6 branch. Its [push CI](https://github.com/RoryGlenn/agent-toolkit/actions/runs/43547834118)
and [pull-request CI](https://github.com/RoryGlenn/agent-toolkit/actions/runs/43547838193)
both passed Python 3.11 and 3.13 checks. The opt-in large-project qualification job was
skipped in these ordinary runs; that skip supplies no runtime qualification evidence.
The PR remains a draft and unqualified. This delivery receipt is a documentation-only
follow-up to that tested code checkpoint.
