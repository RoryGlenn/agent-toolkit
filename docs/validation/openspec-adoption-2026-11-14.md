# OpenSpec adoption assessment

Issue: [#18](https://github.com/RoryGlenn/agent-toolkit/issues/18).
Baseline: `f24fc4193911768f0b0fe3dea2df50ea642d6295`.
Contract and sole progress record: [complete-openspec-adoption](../../openspec/changes/archive/2026-11-14-complete-openspec-adoption/).
Exact assessed runtime/test identities and upstream hashes: [source snapshot](openspec-adoption-source.json).

## Outcome and decision

Continue **direct, opt-in use for substantial changes**, with a narrower maintenance
claim: OpenSpec replaces planning mechanics and a repeated instruction checklist; this
exercise does not establish lower total maintenance, better model quality, speed or cost.
Keep ordinary projects and trivial edits on their existing path. Do not change broader
defaults or remove catalog packages based on this result.

The substantial exercise implements #16 phase 1: safe explicit project reconfiguration
and retirement. It distinguishes requested roots from dependencies, migrates v1 only
after an explicit complete selection, retains historical ownership for absent packages,
previews removals, and reuses preflight and ordinary-error rollback. Personal synchronization,
the broader integration suite and optional metadata consolidation remain in #16.

This assessment records local acceptance before delivery. At that point the candidate
was uncommitted and unpublished, personal configuration was unchanged, and #18 was open.
The user subsequently authorized commit, push, PR creation and merge on 2026-11-14.
The PR and issue history record delivery and hosted checks separately; neither the
earlier merged pilot nor these local checks establish that this candidate passed CI.

## Ownership and actual simplification

| Responsibility | Owner and disposition |
| --- | --- |
| Artifact templates, planning graph, task tracking, synchronization, archive | Upstream OpenSpec 1.16.0, used directly; no adapter or new skill |
| Accepted scope, original requirements, product decisions | Project maintainers; conflicts are surfaced before dependent implementation |
| Implementation, domain judgment, source inspection and useful tests | Existing toolkit skills and one writer; retain these responsibilities |
| Independent review, verification and exact-source evidence | Separate review/verification workers; structural specification checks are insufficient |
| Project copies, ownership, selection, dependencies and recovery | Existing installer; extend its transaction for explicit reconfiguration |
| Ordinary projects and trivial tasks | Existing proportionate path, without an OpenSpec dependency |
| Installation/default changes and external delivery | User authorization and existing repository rules |

The implementation skill's former Required inputs, seven-step Workflow, Completion standard
and six-part Final response lists repeated the same contract/handoff/evidence facts.
They are replaced by one contract section, one common handoff description and one
evidence-based delivery section. Opted-in projects hand planning and lifecycle operations
to upstream instead of maintaining another checklist in the issue/PR. The ordinary-project
fallback remains self-contained. Independent review/release skills remain because their
engineering/artifact judgments are not replaced by specification structure.

No installed catalog capability is retired by this change. The new migration supports
future deliberate retirement, but its existence is not permission to delete a user's
files or remove additional capabilities. All seven tracked generated files under
`.agents/skills/` retain their baseline bytes and stay outside the installable catalog.
Frozen pilot evidence is unchanged. Existing unrelated active changes remain active.

## Maintenance observations

At the first complete implementation, the workflow entrypoint changed from **155 to 93
lines** and **7,295 to 5,693 bytes**: 62 fewer lines. This counts text, not proven
maintenance effort.

Other categories are separate: installer/bootstrap code grew by 39 lines, the new
reconfiguration tests added 296 lines, public evaluation cases added 44 lines, README
grew by 49 lines, and repository guidance added six lines. The source snapshot records
exact counts for project-owned proposal/design/spec/task records separately. This
assessment and its source snapshot add review evidence; upstream-generated content adds
zero changed lines. Overall source volume increased. The migration is needed lifecycle
work, not a demonstrated OpenSpec saving, and its tests are an ongoing obligation.

Remaining costs include reviewing OpenSpec upgrades and regenerated hashes, maintaining
project specifications and task records, checking compatibility/refusal/recovery behavior,
and reassessing changed toolkit skill contracts. Generated workflows are upstream-owned,
but pinning, testing and deciding to upgrade remain project responsibilities. No wrapper
maintenance is introduced. There is no controlled timing, usage/cost, reliability or
long-term upgrade comparison for this exercise.

## Observable adoption cases

| Case | Observation and limit |
| --- | --- |
| Substantial OpenSpec work | This change uses the upstream CLI for proposal/spec/design/task instructions and one task record; one parent writer, separate design/documentation consultation and independent acceptance. All eight tasks completed and the verified upstream sync/archive readback is recorded below. |
| Ordinary project | Disposable bootstrap/reconfiguration installs and checks run without OpenSpec configuration. No OpenSpec package/configuration appears in generated toolkit selection. A separate skill actor planned an ordinary parser fix in existing project guidance without requiring OpenSpec. |
| Trivial edit | A separate actor, after actually reading the changed skill and routing guidance, answered `the` to the one-word spelling request with no delegation or implementation ceremony. |
| Conflicting requirements | The same actor surfaced the 1–100 versus 0–100 conflict and unauthorized remote publication before dependent implementation, keeping the accepted user requirement authoritative. This is an advice smoke case, not an executed conflict-resolution integration. |
| Missing tooling | The verifier ran all 48 CLI probes with OpenSpec absent from PATH; ordinary installation and useful checks remained usable. The actor separately described honest missing-CLI handling for a selected change, without claiming upstream validation/sync/archive. That selected-change response is a simulated advice case, not an upstream run. |
| Coexistence and fallback | The verifier copied all seven actual generated files into a project and proved their bytes survived reconfiguration. Source hashes remain unchanged; tests also preserve shared dependencies/roles, team notes and instructions. Successful CLI installation is not proof of host discovery. |

The four short actor cases were presented together to one fresh generic worker without
parent conversation history. It read the actual changed implementation and routing skills;
it was instructed not to read evaluation/oracle files. This is one shared-context smoke
session, not four independent trials, a blinded benchmark or automatic routing evidence.
Public cases are retained in the existing skill's `evals/evals.json`.

## Handoffs, assessment and rework

The parent owns all source edits. A named software-design specialist inspected the
existing transaction and recommended the v1/v2 boundary and conservative ordinary
updates. Documentation used a separate generic worker reading both the installed
standalone Doc Agent and toolkit documentation guidance. This session lacks the toolkit's
named documentation/reviewer/verifier roles; generic fallbacks are identified rather than
described as named-role execution. Workers inherit the caller's settings; no model change
or external evaluation service was introduced. DDIA migration guidance was read directly;
no DDIA named-worker execution or original-book consultation is claimed.

The design handoff caught a consequential edge case before acceptance: ordinary updates
must retain old dependencies even after the dependency graph changes. Reconfiguration
alone can prune them. A regression now exercises this distinction. The documentation
worker found no blocking migration inaccuracies and executed README preview/apply/check
against both a v2 project and the published v1 fixture, including host-only reconfiguration;
each integrity readback reported 36 managed files and the routing block intact. Its only
open link was this not-yet-created assessment, now supplied.

The initial full-suite baseline had nine pre-existing sandbox/kernel errors; the task
record was corrected to distinguish available gate passes from unavailable environment
checks. No product assertion, sandbox restriction or failure was weakened to obtain a pass.
Independent read-only source review found no actionable findings across all 17 candidate
files and passed the 13 new regressions. The separate verifier reproduced all available
gates and 48 CLI flows in a byte-matched clean package. Its verdict is **partially_verified**
because the same nine kernel checks remain unavailable and hosted Python 3.11/3.13 CI
has not run. Neither source readiness nor local archival waives those gates.

Verifier rework is retained: an initial nonexistent routing pattern ran zero tests; the
corrected pattern ran 13. An initial retired-file fault control detected the defect but
caused later subtest setup errors. Two isolated controls replaced that ambiguous harness:
bypassing collision refusal and pruning dependencies during an ordinary update each caused
one precise assertion failure. The unchanged clean package passed all 13 tests afterward.
Neither unsuccessful verifier invocation counts as a passing product check.

### Changed skill semantic assessment

| Contract | Source assessment |
| --- | --- |
| T01 job/routing | supported: accepted substantial implementation, shared routing pointer, ordinary/trivial paths and opt-in boundary |
| T02 useful expertise | supported: one writer, exact handoffs, real regression checks, independent acceptance and upstream lifecycle delegation |
| T03 grounding | supported: original scope/authorization wins; source-as-data boundary and changed-byte evidence invalidation retained |
| T04 completion | supported: criteria map to actual behavior, independent findings, exact commands, limits and delivery status |
| T05 evaluation | bounded evidence: actual lifecycle exercise and four shared-context advice smoke cases; no claim of general effectiveness |
| T06 ownership | supported: independent workers, read-only reviewer, sole writer, explicit external-action boundaries and truthful fallback |
| G01–G04 | supported where applicable: shorter conditional entrypoint, no wrapper, no forced setup for ordinary/trivial work; original domain checks retained |

Parent source assessment applies to the exact hashes in the snapshot. Prior routing and
engineering assessments retain their original hashes and limitations; their historical
resource manifests are not silently rebound to this candidate.

## Verification and delivery evidence

Independent checks: 13 new reconfiguration tests, 29 bootstrap tests, 13 routing tests and
60 personal install/restore tests passed. All 48 CLI probes and two precise fault controls
passed, including actual source provenance recalculation and real CLI late-failure rollback.

| Command (existing locked environment) | Result |
| --- | --- |
| `uv run --no-sync python -m unittest discover -s tests -v` | 346 run: 337 passed, nine baseline-matched errors; exit 1 |
| Same unit command against pristine Git archive | 333 run: 324 passed, identical nine errors; exit 1 |
| `uv run --no-sync ruff check .` and `ruff format --check .` | Passed; 70 Python files formatted |
| `uv run --no-sync mypy` | Passed, 41 source files |
| `uv run --no-sync python authoring.py check` | Passed, 23 artifacts; structure only |
| `uv run --no-sync python -m skill_authoring verify-upstream` | Passed, pinned upstream identities |
| `python3 install.py check` | Passed, 16 skills/seven Codex roles/zero Copilot roles |
| `uv run --no-sync python -m benchmarks validate` | 13 reference/wrong phase pairs passed |
| `uv run --no-sync python -m benchmarks validate --matched` | 20 reference/wrong pairs passed |
| `git diff --check` | Passed |
| Strict OpenSpec validation before synchronization | Eight current items, three historical archives and all three copied archived delta contents passed |

Verification used Python 3.12.3, uv 0.10.2 and OpenSpec 1.16.0. Full local command logs,
48 CLI receipts, fault controls, pristine baseline and source-bound independent reports
are retained separately from the publication candidate. The source snapshot contains the
sanitized results and exact failed-test identities. Only task/report/spec metadata changes
followed this acceptance; runtime/test/skill bytes remain the verified bytes.

The unchanged baseline ran 333 tests: 324 passed and nine errors. Seven bubblewrap
tests failed establishing namespace/loopback isolation; two kernel qualification tests
failed the nested-storage boundary or read-only evaluator setup. These errors prevent
claiming a fully green local suite. They are unrelated to bootstrap selection behavior.

### Synchronized and archived result

`openspec archive complete-openspec-adoption --yes --json` exited zero, synchronized
**eight added and one modified requirement**, and archived the completed change as
`2026-11-14-complete-openspec-adoption`. Its sole task record has eight of eight tasks
complete. The active change no longer appears in `openspec list --json`.

Afterward, `openspec validate --all --strict --no-interactive --json` passed **9/9**
current items and `openspec validate --archived --strict --no-interactive --json`
passed **4/4** archives. Existing and new specification purposes matched their original
or delta text, and main specs contain canonical requirement/scenario headings. All
previous active change records, seven generated files and frozen pilot evidence retain
their baseline bytes. Local lifecycle completion is verified; hosted CI and remote
publication remain separate and unverified.

## Issue acceptance map

| #18 criterion | Concrete evidence |
| --- | --- |
| Responsibility map | Ownership table and retained/removed guidance above |
| Direct use before adapter | Actual upstream CLI instructions and unchanged generated skills; no wrapper |
| Substantial complete lifecycle | #16 phase 1 implementation, this change's contract/tasks, independent acceptance and final archive readback |
| Removed/added material and costs | Measurements and source snapshot, with no total-saving claim |
| Ownership coexistence | Historical manifest validation, old/new preflight, shared-resource and unowned-content tests |
| Five usage paths | Observable case table and actual migration/ordinary flows |
| Missing tooling honesty | Skill contract and explicit advice-smoke limit; existing checks remain available |
| Relevant checks and updated reviews | Verification section and changed skill's adoption inventory entry |
| Opt-in unchanged defaults | CLI changes only under explicit reconfiguration; default selection and personal setup unchanged |
| Handoff/rework/overhead evidence | Consultation, independent acceptance, failures and maintenance categories above |
| Continue/adjust/stop decision | Continue narrowly and adjust the maintenance claim; broader defaults remain separate |
