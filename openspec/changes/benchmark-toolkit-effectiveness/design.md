# Design

## Context

The existing [development benchmark](../../../benchmarks/README.md) has twelve
public RecordBatch tasks, correct and wrong controls, a frozen attempt schedule,
isolated Codex execution, and artifact-bound grading. Its toolkit arm stages an
isolated personal installation, and its source-enabled arms receive an extra
prompt paragraph. The default project bootstrap requires its own staging path
and a prompt shared by every arm.
The earlier [DDIA pilot](../../../skills/ddia-skill/evals/pilots/issue-8/README.md)
scored ordinary Codex and the redesigned specialist 40/40 on one response each.
The one-file review fixture has a verified rollback failure, and the managed
Linux host stopped both live reviews at sandbox initialization.

## Goals and scope

Measure three outcomes independently: the value of installing the toolkit for
normal use, the value of selecting a named specialist for a task, and the
contribution of that specialist when delegation is already part of the workflow.
Use the existing benchmark CLI and a Markdown report. The first release applies
to Codex CLI and uses project-bootstrap installs. Existing development runs keep
their own plan format and provenance. CI stays deterministic and credential-free.

## Comparison design

| Comparison | Control | Treatment | What it measures |
| --- | --- | --- | --- |
| Full toolkit, primary | Stock Codex with native delegation available | Default Codex project bootstrap with native delegation available | What users gain from a default install and natural routing |
| Full toolkit, single-agent control | Stock Codex with child agents disabled | The same default toolkit condition | What users gain compared with working in one session |
| Per role, user-facing | Stock Codex completes the task in one session | A named worker completes the same task via native dispatch with the needed skill packages | Whether selecting this specialist workflow pays off for the task |
| Per role, controlled | A generic worker in the same delegation slot | The named worker with its associated skill guidance | What specialist instructions and skill guidance add beyond delegation |

Run the per-role conditions as a three-arm block. Freeze the worker brief and
available evidence across all three. In the delegated paths, use the same
coordinator handoff, child count, permissions, and result capture. The coordinator
passes the prewritten task through and captures the worker's answer or artifact
before synthesis. Verify the assigned scope and input identity through the
available trace. Change the worker assignment and associated skill guidance
between the delegated arms. For a role that operates on a prior implementation,
stage the same frozen input in every arm.
Treat named role instructions and their associated skills as one intervention.
Use the existing source-matched approach for any optional book-source comparison.
The initial campaign uses public project data and packaged guidance with source
availability recorded explicitly.

Keep the actual model and reasoning effort, task bytes, interpreter, task tools,
external resources, elapsed-time limit, and effective permissions matched.
Hash the complete user prompt and original product fixture. Fingerprint the
treatment layer separately. Record client version, OS, package commit, observed
dispatch, source access, and inherited settings. Use fresh sessions and rotate
arm order in each scheduled block. Preserve the current harness's controlled and
shipped setting distinction in any supplemental results. Compare stock native
delegation separately from the explicit single-agent condition. If a comparison
claims an equal enforced compute cap, first verify session-tree budget exhaustion
on the selected runtime. Otherwise, publish the shared wall deadline and the
actual observed usage for each arm.

## Tasks and grading

### A one-file demo

Start from the verified `ledger.py` example. The patch replaces two `execute()`
calls with `executescript()`. Python 3.11's legacy behavior, or an explicit
`LEGACY_TRANSACTION_CONTROL` connection in newer Python, commits pending caller
work before the script runs. Use a clean diff that reformats the two statements
while preserving the separate calls. Keep the reference, rollback probe, and
grading instructions outside the actors' projects. The public demo uses two
read-only workspaces, one changed Python file, and exactly **“Review this diff.”**

Grade both cases against the same review rubric. A seeded finding needs the changed
line, caller-owned transaction, implicit commit, and persisted row after rollback.
Track actual reproduction, the proposed correction, and unsupported material
findings separately. Grade extra findings on evidence. For the clean case, a
fabricated rollback defect fails the review. The executable result is zero rows
for the reference and clean diff, one for the seeded diff, and successful table
and index setup in all three. The smoke run is informative whether both, either,
or neither model catches the seeded defect.

### Role coverage

Reuse public RecordBatch and legacy-code cases for development. Freeze original,
unseen tasks before a confirmatory run. The table identifies a positive task,
adjacent or failure case, and observable grading surface for each role.

| Named Codex role | Case and control | Primary evidence |
| --- | --- | --- |
| `ddia_agent` | Retry after commit and acknowledgment loss. Include a clean idempotent variant and a concurrent admission case. | Durable effect counts, replay and concurrency checks, correct account of the guarantee |
| `documentation_agent` | New-user quickstart or archive recovery. Include an example that prints success but omits a necessary setup step. | Fresh-environment execution to the stated outcome, independently assessed clarity and accuracy |
| `software_design_agent` | Extend an iterable-based API while preserving existing callers. Include a simple local fix that needs no new abstraction. | Caller compatibility, a frozen follow-up change, independently assessed maintenance burden |
| `legacy_code_agent` | Change a poorly tested path with a hard-to-isolate dependency. Include an alternate path already covered by a useful test. | Characterization detects an incorrect rewrite, accepted behavior changes, unrelated paths stay intact |
| `implementation_owner_agent` | Implement a scoped cancellation or status-filter change. Include a request where neighboring cleanup is tempting. | Acceptance and regression tests, diff scope, existing contracts |
| `adversarial_reviewer_agent` | Inspect frozen seeded and clean diffs, including rollback. | Grounded detection and severity, false positives, corrective action that preserves the contract |
| `verifier_agent` | Check an exact release artifact with a missing dependency or wrong revision alongside a clean artifact. | Independent command evidence, correct artifact identity and verdict, unsupported claims caught |

Use actual per-role skill dependencies from the installer. The optional legacy
role gets a selectively bootstrapped treatment. Include at least one ordinary
small task in the full-toolkit suite to measure unnecessary delegation and
changes outside scope. Use held-out project contexts beyond RecordBatch and
keep the hidden case list, grades, and probes in the curator workspace until
the campaign is complete.

Choose the primary success rule per task before any actor run. When feasible it
requires executable acceptance and no material regression. For qualitative work,
use a short anchored rubric and blind grading of frozen outputs. Give the graders
the task, expected behavior, rubric, and supporting evidence. Withhold arm labels
and identifying traces. Record potential unblinding, review disagreements, and
their resolution. Two independent graders score judgment-based confirmatory
outputs before labels are revealed. Record an independent adjudication if their
scores still differ. For every case, verify a correct control and at least one
wrong or misleading control. Keep `needs_review` separate until it is resolved.

## Harness changes

Extend `benchmarks plan/prepare/run/report` with a versioned comparison plan.
Reuse the existing scheduling, fingerprints, process deadline, session evidence,
artifact sealing, and report grouping. Keep the legacy plan reader and its
arm-specific prompts for historical runs. For new plans, construct the actor
prompt once per task. Derive installed guidance from the canonical bootstrap
and dependency inventory. Enumerate actual roles rather than copying the count
in the development README.

The demo needs a bounded local Git fixture and real project instruction discovery.
Enable project instruction ingestion only for the isolated new profile. Stage
the authorized baseline commit and diff in each review workspace, with no remote
or parent Git configuration. Fingerprint the reference, staged diff, exact
guidance, plan, and rubric before running. Extend the current preflight to check
the Git diff, project instruction boundary, expected role visibility, and the
separation between review workspaces, expected outcomes, and controller files.
Retain the existing permission controls and separate grading execution. Set the
read-only roles' product files read-only on the host while allowing permitted
temporary output. Distinguish role discovery, skill reads, native dispatch, and
successful task execution in the evidence. If native worker output or dispatch
cannot be attributed, retain the run and leave the role claim unverified.

Build the public report from sealed results using a narrow allowlist. Include
task and artifact identifiers, prompts, sanitized final outputs and grading
receipts, elapsed times, and observed model and tool use. Include raw attempt
logs only privately. Treat source excerpts, credentials, environment paths,
private repository material, and raw sessions as private. The report should be
regenerable from its sanitized inputs.

## Pilot and publication

| Stage | Proposed starting scope | Decision |
| --- | --- | --- |
| Demo | Seeded and clean SQLite diffs, two headline arms, one fresh pair per diff | Confirm usable onboarding, stock access, native toolkit discovery, and visible grading evidence |
| Calibration | Four end-to-end tasks with two arms and two attempts each, plus two tasks each for reviewer and DDIA with three arms and two attempts each | Inspect 40 planned actor sessions across the two calibration blocks, ceiling effects, setup failures, grader agreement, and cost |
| Confirmatory | Held-out tasks across the full workflow and every named role. Set distinct-task counts, repetitions, and campaign limits after calibration and before any confirmatory outputs. | Publish supported claims per host, model, and treatment with the complete denominator |

The counts above are planned root sessions. Child calls add observed work. Start
the smallest live run on Ubuntu or macOS where native canaries pass, using an
existing signed-in Codex profile. For calibration, start with one supported
model at medium effort and a 180-second actor deadline per slot. Record the
exact model before the run. These settings bound sequential actor time for the
40-session calibration at two hours, with setup and grading measured separately.
A blocked host produces a setup result with the failed check. Freeze the task
list, scoring rule, condition order, smallest useful lift, cost ceiling, and
analysis before the confirmatory run. Size it using pilot variation and the
number of distinct tasks. If the available sample cannot support a claim, label
the results exploratory.

Report success counts, paired wins/ties/losses, miss and false-positive counts
where relevant, incomplete pairs, and unresolved grading. For the primary
comparison, average matched success differences within each task, then weight
distinct tasks equally. Estimate uncertainty by resampling tasks with their
repetitions together on a frozen seed. When tasks share a project or differ only
by a related failure case, resample the project or case family as a cluster.
Require the lower 95% confidence bound to exceed the predeclared useful lift for
a positive claim. For simultaneous confirmatory claims across roles, freeze a
multiple-comparison adjustment before running. Use intervals only where task
count and sample design support them.
Count scheduled timeouts and failures in end-to-end coverage. Report explicitly
which attempts support the quality estimate. Run a sensitivity check that
assigns missing comparisons unfavorable outcomes for the claimed condition.
Keep the full scheduled denominator visible next to the eligible quality
denominator.

Publish elapsed time and run-wide tokens where observable, separately from
grading overhead. An estimated dollar figure needs complete run-wide usage and
a dated price basis. Report root-only usage and missing child telemetry as such.
Lead the README with the reproducible demo and the strongest supported result.
Link a table with all role outcomes, neutral and unfavorable cases, model and
host settings, and the exact test commands. Keep reports for different hosts and
models separate. Preserve prior reports by revision. Give each role row a
consistent set of fields for the task family, stock and named success counts,
generic-worker comparison, uncertainty, median elapsed time, and token coverage.

## Risks and trade-offs

| Risk | Response |
| --- | --- |
| Stock Codex readily catches the known SQLite regression | Show the actual demo outcome. Use the held-out suite to test harder work. |
| More workers also means more compute | Include the matched generic-worker comparison and show quality next to whole-run resource use. |
| Expertise seems to help only when explicitly invoked | Use natural prompts in the full-toolkit arm, and report actual routing separately from named-role performance. |
| Public cases become tuning examples | Keep public examples for calibration. Freeze held-out cases before scoring and release them with the published revision where possible. |
| A new CLI obscures traces or fails native isolation | Qualify the exact host/version/configuration, record unavailable evidence, and preserve aborted slots. |

## Rollout

Land the demo, deterministic checks, and versioned runner path first. Run the
bounded pilot on the qualified host, and freeze a new confirmatory plan after
calibration. Add quantitative README claims after reproducing the report from
sanitized receipts. Revision the README links and reports together, so a future
toolkit release can retain the earlier evidence and show its own results.
