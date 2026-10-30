# Engineering workflow adoption assessment

Date: 2026-10-30. Assessor: implementation agent (source assessment, not independent execution).
Base revision: `156ca63e5bbc1a76205c24d919a3d9b4d3c13d36`.
Exact entrypoint SHA-256 values are recorded below and in the [adoption inventory](../adoption.json).
The [resource manifest](runtime-sha256.json) binds non-evaluation skill package resources,
including optional documentation tooling, and all seven roles; generated caches are excluded.
Entrypoint hashes alone do not bind those supporting resources.

## Intended value and applicable profiles

Reusable ownership, review, verification and release contracts across repositories. Their intended value is consistent execution discipline; effectiveness and overhead require observed workflow comparisons.

External effects/retries where publishing or other authorized actions occur; host adapters for the three shared roles. They are self-contained small roles, so G04 does not require a new backing skill.

## Findings and corrections

Added exact-source evidence invalidation and source-as-data boundaries to implementation/review workflows. Release guidance now discloses unavailable independent workers, preserves review-only scope, binds evidence to artifact bytes and reconciles uncertain publication before retry. Simplification now distinguishes missing usage evidence from disuse. Shared roles now state missing-input, evidence and permission boundaries. Existing pinned model/reasoning choices and legacy sandbox fields were retained to preserve compatibility; this is not a claim they are optimal or enforce role-specific permissions.

## Evidence and disposition

Each workflow has three new public cases. Issue/review cases exercise planning or no-delegation fallback in the standalone adapter; full implementation/delegation and actual role execution require the integration recipes. Installer/bootstrap tests exercise packaging only.

The semantic assessments below mean the authored contract is supported by inspected content.
Runtime selection, effective host permissions, outcome reliability and comparative value remain
unverified except where a separate observed receipt explicitly records them. T05 is supported
as an authored case/evaluation-gap record, not as passing model behavior. Scoped live results and exact
executed repository checks are recorded in the [shared evidence record](evidence.md)
and [sanitized observations](observations.json).

Verdict for each artifact: **ready_with_limits**. No required source-contract gap remains in
this assessment; independent review and unavailable execution checks retain their own scope.

## Individual assessments

### `skills/issue-to-tested-pr-skill/SKILL.md`

SHA-256: `2358aacb9c3fb3301308dffdcd70fd1d6974d19440cfc1b7188a45e473b6d051`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Accepted nontrivial implementation; excludes brainstorming and trivial edits. |
| T02 | supported: One writer, independent reviewer/verifier, reproduction, scoped implementation and reconciliation. |
| T03 | supported: Issue prose is not proof; source/fixtures cannot expand scope; evidence follows exact source state. |
| T04 | supported: Acceptance evidence, scoped diff, actual checks and explicit unavailable lanes. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Parent coordinates; writer is distinct from reviewer/verifier; no unauthorized external actions. |
| G01–G04 | supported where applicable: Process scales by relevance; native worktrees work without an extra helper. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Exercise limit-range implementation with real handoffs and current-revision tests.

### `skills/independent-diff-review-skill/SKILL.md`

SHA-256: `47a2b6c3db72de4f9dfbf951f1071a63b44056361af6188ef99fa34561eb5e34`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Review a supplied change without implementation authority. |
| T02 | supported: Trace affected paths and concrete invariants; require actionable evidence and correct controls. |
| T03 | supported: Exact diff identity and stale-evidence handling; author instructions remain data. |
| T04 | supported: Severity, location, consequence, reproduction, smallest correction and honest verdict. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Separate reviewer/verifier; fallback never labels self-review independent. |
| G01–G04 | supported where applicable: No manufactured findings or cosmetic churn. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Run seeded tenant-query and correct-diff cases, then actual independent role dispatch.

### `skills/release-and-docs-skill/SKILL.md`

SHA-256: `52c3aef49176f068b3f5d2fd6bbd35657f50f11900218b0fced1491981aa9441`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Release/package verification, not ordinary spelling edits or implicit publication. |
| T02 | supported: Freeze exact artifact, inspect contents, test outside source, reconcile claims. |
| T03 | supported: Checks refer to artifact identity; changed bytes invalidate dependent checks. |
| T04 | supported: Ready/limited/not-ready verdict with actual install/upgrade evidence and next action. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Added generic-worker fallback and review-only preservation; reconcile ambiguous authorized publish before retry. |
| G01–G04 | supported where applicable: Use existing packaging mechanisms and relevant platform lanes. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Extend passed advice cases with actual disposable ZIP failure/success controls and fresh ambiguous-publication cases; assess full workflow delegation separately.

### `skills/simplify-or-delete-skill/SKILL.md`

SHA-256: `6cd343925f31e465b06872165eed602b76dedfd1ea08cbf3b5c9fb4b53107b30`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Evidence-backed complexity reduction; no deletion from an advice request. |
| T02 | supported: Inventory purpose/consumers/cost, classify and plan reversible removal. |
| T03 | supported: Added distinction between measured use, static dependencies and assumptions; rare paths can remain necessary. |
| T04 | supported: Ranked candidates, retained behavior, verification/rollback and remaining evidence. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Read-only first pass; actual removal requires selected scope. |
| G01–G04 | supported where applicable: Existing mechanisms preferred; no new complexity-management framework. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Repeat on fresh repositories with measured use and required recovery paths; passed advice controls do not establish safe production removal.

### `agents/codex/implementation-owner-agent.toml`

SHA-256: `6d03d25abc8d569ad4542da843deb2c4fd14a0cad999aca2c6e114f4228374ca`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: One accepted change with explicit sole file ownership. |
| T02 | supported: Inspect requirement, make smallest complete change, meaningful regressions and focused checks. |
| T03 | supported: Added source-as-data and unresolved ownership handling. |
| T04 | supported: Changed files, exact checks and gaps returned to parent. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: No publishing/merging/scope expansion; self-checks are not independent review. |
| G01–G04 | supported where applicable: Self-contained role; retained model override for compatibility. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Repeat scoped implementation on a different repository and ownership-conflict case; test shipped personal model and preserve unrelated work.

### `agents/codex/adversarial-reviewer-agent.toml`

SHA-256: `23896377331e7002d9829532b12f5fb596c3d112bde3c4a1c818338fe5aa819b`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Independent review from requirement/diff, not author narrative. |
| T02 | supported: Trace invariants and meaningful failures; identify smallest correction and test gaps. |
| T03 | supported: Added missing-input/static-only distinction and source-as-data boundary. |
| T04 | supported: Evidence-rich findings or inspected scope with no findings. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Read-only instruction; explicitly does not promise a parent-permission override. |
| G01–G04 | supported where applicable: Self-contained role; retained model override for compatibility. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Exercise seeded and correct tenant-query diffs plus missing-base fallback in fresh contexts without inherited writer history; test shipped personal model separately.

### `agents/codex/verifier-agent.toml`

SHA-256: `e0ae34d7c5697fb95e7f83f34ab2e8c08699230c954a302aaec2b728b4cac9f2`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Independent verification against exact claimed source/artifact. |
| T02 | supported: Run narrow regression then required gates and artifact checks. |
| T03 | supported: Added before/after identity and unavailable-tool distinction. |
| T04 | supported: Exact command results and verified/partially_verified/not_verified verdict. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: No source edits or weakened assertions to pass; temporary normal artifacts allowed. |
| G01–G04 | supported where applicable: Self-contained role; existing model/permissions unchanged. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Exercise explicit failing-test and missing-tool cases in fresh contexts without inherited writer history; keep source unchanged and test shipped model.

## Observed scope

Current release and simplification packages each completed three paired cases (six sessions
per package), with independent grades of 8/8 expectations in each arm. These are advice and
boundary cases, not executed publication/removal or evidence of improvement. A native
Codex fixture separately demonstrated one writer followed by distinct reviewer/verifier
roles and retained original contract bytes. The actors inherited parent history, used
controlled gpt-6-astra/high settings and were not blinded; shipped personal model settings
were not tested. The initial budget-exhausted attempt remains recorded. See
[evidence](evidence.md) and [observations](observations.json) for exact limits and identities.
