# Global Agent Toolkit rollout verification

This is the historical snapshot of the initial local rollout, before the checked
updater and Git delivery. Counts, hashes and setup results below describe base
`3827a69` plus that rollout's uncommitted source; they do not identify the later
combined delivery. The user subsequently authorized
[issue #33](https://github.com/RoryGlenn/agent-toolkit/issues/33). The companion
[updater completion record](../../openspec/changes/archive/2026-11-14-add-safe-global-toolkit-updates/tasks.md)
records its separate scope and validation. Keep this earlier evidence, including
its failures and unavailable checks, rather than replacing it with later results.

Checked 2026-11-14 on the workstation's default local Codex profile. Global
installation and explicit task routing are enabled, with a local evidence audit.
Fresh CLI and IDE integration checks establish real named-agent use. Desktop UI
execution remains unverified, and the broader synthetic numeric experiment did
not complete within its bounds. These limits are retained below.

The detailed [OpenSpec plan and implementation record](../../openspec/changes/archive/2026-11-14-enable-global-toolkit-dogfooding/proposal.md)
was completed before implementation, tracked through 25 tasks, synchronized into
two main specifications, and archived with strict specification validation.

## Persisted setup

| Item | Verified result |
| --- | --- |
| Retained source | Primary checkout at base `3827a69364da2c89e770eedcf19866654fff8db8` plus this uncommitted local change. |
| Personal catalog | 16 toolkit skills and seven named roles; all 23 expected entries `current`. |
| Compatibility | All 26 original standalone Doc Agent file hashes unchanged at its established path. |
| Global policy | Original global guidance retained, followed by exactly one managed routing block. |
| Configuration | Original Codex configuration hash unchanged; permissions and parent model defaults preserved. |
| Recovery | Receipt-backed installation, private pre-change snapshot, and disposable full install/status/restore verified. |
| Portable policy | Private dotfiles template, guarded policy installer, recovery instructions, and three tests. |
| Prior work | Original pending toolkit/dotfiles contents retained; previous source worktree remains clean. |

The new `--preserve-legacy-skill doc-agent` option keeps the independent standalone
workflow while installing the canonical documentation skill and named role. It
does not suppress canonical destination conflicts or change normal migrations.
Repeat it on future installations when the compatibility package must remain.

A real request using the implementation owner's old `gpt-5.6` pin failed because
the account did not support that model. Only that role's obsolete model and effort
overrides were removed. It now inherits the caller; its instructions are unchanged.
Actual named execution used `gpt-6.1-sol`, while reviewer/verifier roles retained
and successfully used `gpt-5.6-terra`. This is a compatibility check, not a
comparative model-quality result.

## Observed execution

Original natural domain prompts named no expected agent. Native parent-linked
child metadata, own terminal events, identifiable successful guidance reads, and
the primary's delivered result were checked separately from installation status.

| Declared case | Observed result |
| --- | --- |
| Documentation | Completed named documentation role; generated guide's export and four failure paths checked; original product inputs unchanged. |
| Software design | Completed named design role; proposed boundary and alternative checked against the fixture. |
| Data guarantees | Completed named DDIA role; duplicate-charge crash counterexample and provider-contract gap checked. |
| Legacy code | Completed named legacy role; proposed constructor seam exercised and missing cancellation contract retained. |
| Explicit no-delegation | Direct design guidance, no child execution. |
| Arithmetic | Exact answer, no tools or children. |
| Fresh IDE task | Supported local task interface produced a fresh `vscode`-source thread, completed named design child, and checked primary recommendation. Native UI appearance was not inspected. |
| Bounded implementation control | Named writer, separate reviewer and verifier completed; 11 fixture tests and 17 separate public-contract checks passed. |
| Broader numeric experiment | Failed/incomplete after 480-second and 720-second coordinator bounds; extreme Decimal handling remained unresolved in the observed workflow. |
| Desktop | Native controls unavailable. Supported installed-binary discovery found core packages and standalone Doc Agent; this is not desktop UI execution. |

The implementation control explicitly restricted inputs to built-in bounded
numbers. It is a separate positive control and does not erase or repair the
broader experiment's result. The failed experiment is synthetic fixture work,
not a feature delivered by this change. Its observed failure remains useful
dogfooding evidence; no universal correctness or latency benefit is claimed.

Selected audit: **20 canonical traces, ten declared cases, eight checked passes,
one failed/incomplete case, and one unexecuted desktop case**. Nine routing cases
were observed and the desktop case explicitly skipped. All seven named toolkit
roles have completion evidence. Zero parse limits; selected trace bytes remained
unchanged during inspection. The audit correctly exits **1** because the declared
failure is retained.

A separate recent-history inspection read 79 traces with zero parse limits and
left 32 root sessions' eligibility unclassified. That selection establishes
observed activity, not an adoption rate. Skills read, agents started/completed,
task eligibility, outcomes, aborted turns, and unclosed historical records remain
separate. Nothing in the report establishes current worker health.

## Source and review

Concurrent upstream OpenSpec changes advanced the source during this work. The
primary checkout was safely reconciled from `f24fc41` to `3827a69`; scoped local
changes merged cleanly. Domain/routing entrypoints and named-role instructions
were unchanged between case batches. The positive bounded workflow control ran
after the implementation skill's upstream update.

Independent generic review and verification were used in the original
conversation because its pre-install catalog could not dispatch newly installed
role names. They are not reported as named-role runs. Fresh CLI/IDE records
separately establish actual named execution. Independent reviewers approved the
source changes and confirmed fixes for a surface-label false pass and a policy
helper's linked-parent escape.

| Initial rollout check | Result |
| --- | --- |
| Repository unittest | 370 run: 361 passed, zero assertion failures, nine baseline kernel errors. |
| Native error controls | The same nine tests failed on a clean retained baseline; no check was skipped or waived. |
| Ruff lint/format | Passed. |
| Mypy | Passed for 42 source files. |
| Authoring/package/whitespace | Passed. |
| Dotfiles tests | Three passed; lint/format and shell syntax passed. |
| Dotfiles restore sample | 15 allowlisted files restored byte-identically in a disposable home. |
| OpenSpec | Active change strict validation and both generated main specifications passed. |

The nine native errors concern unavailable network-address, mount-propagation,
and cgroup enforcement controls in this execution environment. This is partial
verification, not a green full-suite result. The unaffected baseline source and
failed run receipts are retained.

Initial rollout audit source SHA-256:
`758f65feb33806b1f00e186d2d5d49f4d5885e4bf93d2f20038901541acc78d6`.
Initial rollout installer source SHA-256:
`5c4a9c8a0f582e0bd75a8115b82620d14d5bdff49daa7ef1689bd1b3754f2e47`.
The independently checked source-manifest SHA-256 before closing evidence and
archive records is `cc9753286578dee864630611bf136a85a9d578fc62af849a880dd40ac90453a5`.
Closing narrative records and archive synchronization were produced afterward;
the tested runtime code remained unchanged within that initial rollout. The
subsequent updater extends the installer; its code has separate source identities.

## Use and recovery

Start a fresh Codex task to get the full installed role catalog. Already-open
conversations can retain the older catalog. Continue using ordinary requests;
the global policy requests relevant named agents for substantive work and keeps
trivial requests direct. Instructions request behavior rather than mechanically
guaranteeing every future invocation.

Run the local audit from any directory:

```bash
python3 ~/repos/agent-toolkit/usage_audit.py --max-sessions 100 --since-hours 24
```

See the [setup, interpretation, and restore guide](../global-dogfooding.md).
Private snapshots, installation receipts, manifests, exact traces, outcomes, test
logs, and readbacks are under
`~/.local/state/agent-toolkit/dogfooding/20261114T144123Z/`. The selected-case report
is `case-audit.json`; `case-audit-receipt.json` binds its source and trace hashes.
The installation receipt is
`~/.local/state/agent-toolkit/installations/20261114T144324Z-251c4d2e4591/receipt.json`.

The audit sends no data anywhere and creates no scheduled job. No new cloud
dependency or permission expansion was introduced. During this initial rollout,
no issue, commit, push, PR, publication, or merge was created; source and
configuration were saved locally with unrelated pending work preserved. Later
Git delivery is tracked separately in issue #33 above.
