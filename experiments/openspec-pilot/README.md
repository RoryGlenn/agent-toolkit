# OpenSpec paired pilot

Date: 2026-10-31. Related: [issue #18](https://github.com/RoryGlenn/agent-toolkit/issues/18).

The existing project intention was sufficient to start this trial. OpenSpec added
feature-level requirements, design decisions, a task record, and a specification
lifecycle around that intention. It did not produce a general coding-quality win
on the three small features tested here.

## Results

One frozen implementation per feature and condition was tested against the same
independently written behavior probes. Both conditions used the current toolkit;
the treatment additionally used OpenSpec's upstream-generated workflows.

| Feature | Current toolkit | Toolkit plus OpenSpec |
| --- | ---: | ---: |
| `list --json` | 7/7 probes passed | 7/7 probes passed |
| `bootstrap --check` | 16/16 probes passed | 16/16 probes passed |
| Personal installation `status` | 12/12 probes passed | 12/12 probes passed |
| Total | 35/35 | 35/35 |

The original unmodified source scored 0/35: every probe requires a successful
positive feature control before testing rejection or failure behavior. Unsupported
commands therefore do not receive credit just for exiting nonzero.

Independent code review added information beyond those probes:

- The current-toolkit project-check candidate accepted missing or malformed
  source provenance in an ownership manifest and reported integrity intact. The
  OpenSpec candidate rejected all three reproduced variants.
- Both personal-status candidates raised an uncaught exception on looping home
  paths. The integrated draft fixes this narrowly and adds regression coverage
  for both `--home` and `--codex-home`.
- Catalog implementations were materially equivalent. Review found complementary
  test strengths, rather than a meaningful architecture difference.

These are observations about six submissions, not evidence that the workflow
caused either a defect or its avoidance. Frozen patches and their original
findings remain unchanged after integration and correction.

## What changed in practice

Your project-wide intention continues to live in the README. Each OpenSpec change
adds a smaller contract. For example, project integrity checking must accept
unowned files and instructions outside the managed routing block, reject edited
owned files, and preserve the filesystem. Those are specific, testable behaviors
inside the broader intention of safe, portable project setup.

The treatment produced 15 planning files totaling **355 lines** across the three
features, before integration. These are requirements, proposals, designs, task
records, and change metadata. The initial snapshots are retained in
`planning-snapshots/`. The six upstream-generated workflow skills contain 1,357
lines; their maintenance belongs upstream. Line counts describe footprint, not
quality or model cost. See [metrics.json](metrics.json).

No custom OpenSpec wrapper, new worker role, orchestration service, or production
dependency was added. No existing custom workflow instructions were removed in
this pilot. Thus a reduction in long-term maintenance is **not yet measured**:
OpenSpec currently adds project records and a maintained upstream dependency.
The next adoption decision is which duplicated planning/lifecycle guidance to
delegate to it, while retaining engineering judgment and independent review.

For this repository, selective use on substantial behavior changes is supported
by the trial. Mandatory use for every small edit is not supported by these data.

## Design and evidence boundaries

- Source commit: `0b36e7d4e95300b16a713edf831c8613dba46b69`.
- Source tree: `173fc826479ad7859d34d106a525b62ba1725a58`.
- OpenSpec: **1.16.0**, standalone Linux x64 release; its published SHA-256 was
  checked. Generated skill fingerprints are in [upstream.json](upstream.json).
- The same accepted feature requirements were supplied to both conditions. See
  [plan.json](plan.json). A shared clarification restricted skill-link matching
  to the existing installer's canonical absolute target.
- Six fresh-context collaborator agents inherited the parent's model/reasoning
  configuration. Actual provider revision, aggregate token use, and cost were
  unavailable; those quantities are unknown. No speed or cost improvement is claimed.
- Each actor used a separate checkout. Scope instructions separated actors from
  sibling outputs and evaluator material, but filesystem isolation was not
  enforced. This is a development pilot, not a sealed benchmark.
- There was one frozen submission per condition/case, with normal implementation
  and test iterations inside that attempt. There were no model retries or
  best-of-many selection. Reviewers received candidate labels and original
  requirements without condition mappings or writer summaries; output contents
  can still reveal clues, so blindness is limited.
- Actors in the treatment read generated propose/apply skills and created change
  artifacts using the real CLI. The user's full planning-and-implementation
  authorization was carried into those tasks; the generated propose skill's
  request for a separate implementation turn was not treated as requiring a
  second user approval during this already-authorized trial.
- Before grading, the verifier corrected the evaluator to check non-mutation
  around the first positive inspection and include modification times. The
  initial reviewed evaluator and its results remain in `evidence/initial/`.
- Final regrading uses a separate fixed original snapshot, verified against all
  **195 original Git blob identities**, so assembly of the integrated draft
  cannot change the reference. `source-manifest.json` records those identities.
  The packaged evaluator was formatted and typed to repository standards; its
  assertions were independently compared with the initial scoring version.
  Both grading passes are retained as different evaluator/source-bound runs.
- The probes cover bounded behavior and observed no-write snapshots. They do
  not establish absence of transient writes, concurrent filesystem substitution,
  every invalid input, host UI discovery, or documentation effectiveness.

The final integrated product uses the three treatment implementations, reconciles
their shared CLI code, and fixes the independently found status-path error.
Integration is a separate source state; its checks are reported separately from
the original paired submissions.

The real CLI synchronized and archived all three integrated feature changes.
Archived validation caught one stale personal-status task checkbox inherited
from the earlier frozen planning snapshot. It was reconciled with the completed
verification logs, and archived validation then passed. Both validation receipts
are retained. Keeping task records accurate is still project maintenance.

## Repository verification

The original baseline ran 203 unit tests with 201 passing and two environment
errors. The integrated product ran **226 unit tests: 224 passed and the same two
environment errors**. Both errors occur while creating `socket.socket()` in
existing native benchmark preflight tests:

- `OracleRegressionTests.test_native_git_inside_repository_stops_parent_discovery`
- `OracleRegressionTests.test_native_grader_cannot_overwrite_protected_alias_target`

This host denies socket creation. These checks remain unavailable; they are not
reported as passed. Installer tests (60), project bootstrap tests (29), Ruff,
formatting, mypy, authoring, package checks, whitespace, and OpenSpec validation
passed on the integrated product. The full-suite log is retained in
`evidence/integrated-unittest.log`.

Earlier setup attempts used `/tmp`, which is a different filesystem here and
caused hard-link failures, then a temp directory inside a checkout, which
correctly triggered source/destination overlap safeguards. A sibling temporary
directory on the same filesystem resolved those setup problems. Initial logs
and the signed-in CLI's read-only-state startup failure are retained separately;
these are infrastructure results, not comparative feature outcomes. Model work
used the available collaborator agents instead of the unavailable nested CLI.

See the original and final independent review records in `evidence/`, and the
final source-bound command receipts and results under `evidence/final/`.

## Reproduce deterministic grading

On your Ubuntu machine, use a checkout of this draft and the development Python
environment described in the root README. Create worktrees **outside** the source
checkout so installation safeguards can operate normally. For example:

```bash
git worktree add --detach /tmp/toolkit-pilot-original 0b36e7d4e95300b16a713edf831c8613dba46b69
git worktree add --detach /tmp/toolkit-pilot-catalog-a 0b36e7d4e95300b16a713edf831c8613dba46b69
git -C /tmp/toolkit-pilot-catalog-a apply "$PWD/experiments/openspec-pilot/evidence/catalog-json-a.patch"
uv run python experiments/openspec-pilot/evaluate.py catalog-json /tmp/toolkit-pilot-catalog-a \
  --baseline /tmp/toolkit-pilot-original \
  --output /tmp/toolkit-pilot-catalog-a-grade.json \
  --scratch-root /tmp/toolkit-pilot-probes
```

Repeat with the six retained patches and their matching case identifiers. The
condition mapping is in `plan.json`. Evaluate the original worktree as a candidate
to repeat the negative controls, or this integrated checkout to test the combined
features. Fixture source/destination pairs are created together on one filesystem.

This regrades saved code without model calls. Repeating the agent comparison
requires new fresh contexts, the recorded feature requests and dependency version,
and a new report of every outcome and available usage. Keep that separate from
these frozen observations.
