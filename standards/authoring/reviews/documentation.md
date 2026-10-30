# Documentation adoption assessment

Date: 2026-10-30. Assessor: implementation agent (source assessment, not independent execution).
Base revision: `156ca63e5bbc1a76205c24d919a3d9b4d3c13d36`.
Exact entrypoint SHA-256 values are recorded below and in the [adoption inventory](../adoption.json).
The [resource manifest](runtime-sha256.json) binds non-evaluation skill package resources,
including optional documentation tooling, and all seven roles; generated caches are excluded.
Entrypoint hashes alone do not bind those supporting resources.

## Intended value and applicable profiles

Consistent reader-task guidance, reusable source/validation boundaries and thin host adapters. This makes the intended process discoverable across projects; it does not demonstrate added value over an unaided model.

Book/reference specialist and host adapters; external effects only when the requested documentation task has them.

## Findings and corrections

The skill initially satisfied the source-level contract and was retained. Live sparse-contract checks subsequently exposed repeated field/mechanism inference despite its broad grounding rule. One compact worked counterexample was added to distinguish an identifier from an assumed JSON property name and acceptance from a presumed execution mechanism/start state; the existing method and fixtures remain intact. Its Codex wrapper already supplies missing-source disclosure. The Copilot wrapper now explicitly handles a missing skill/resource and continues only from available product evidence. A subsequent live smoke selected the role but listed directories without reading the present skill, then supplied unspecified API details. The startup instruction was clarified to require an actual SKILL.md read before substantive output, exact fallback attempts and disclosure of the attempted path/error when a read fails. Listing a directory is explicitly distinguished from loading guidance. Tools and model inheritance remain unchanged.

## Evidence and disposition

Existing four documentation fixtures, the environment checker tests, and the new three-case `evals/evals.json` using existing Roster/Pulse inputs. The optional browser regression restoration remains outside this migration. Structural success is not browser accessibility or real-reader success.

The semantic assessments below mean the authored contract is supported by inspected content.
Runtime selection, effective host permissions, outcome reliability and comparative value remain
unverified except where a separate observed receipt explicitly records them. T05 is supported
as an authored case/evaluation-gap record, not as passing model behavior. Scoped live results and exact
executed repository checks are recorded in the [shared evidence record](evidence.md)
and [sanitized observations](observations.json).

Verdict for each artifact: **ready_with_limits**. No required source-contract gap remains in
this assessment; independent review and unavailable execution checks retain their own scope.

## Individual assessments

### `skills/documentation-skill/SKILL.md`

SHA-256: `54a2cfc4ac454196ff98bdae700bc8b6d44d8066e387c8bdc1b55b19bbcca52a`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Reader success in write/revise/review/plan/maintain modes; a translation or spelling correction needs no full documentation workflow. |
| T02 | supported: Audience discovery, content patterns, source-based examples and accuracy-before-polish provide concrete procedures. |
| T03 | supported in revised source: product evidence and book synthesis distinguish observation from assumptions; a worked counterexample now preserves sparse-contract schema/mechanism precision. The final Pulse pair and two Copilot cases passed with the limits in the shared evidence record. |
| T04 | supported: Deliver requested content or actionable review, exact relevant checks and material gaps. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Review-only mode preserves files; external effects require actual authorization. |
| G01–G04 | supported where applicable: Retained conditional reference loading and optional tooling. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Repeat Roster/translation on the final runtime and add fresh sparse-contract/export-review cases; independently assess real-reader usefulness.

### `agents/codex/documentation-agent.toml`

SHA-256: `d33001a64b717363511a935615ace790e07650a626b2d684401a33ec88740fc5`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Delegate substantial documentation work to a separate owner; do not recursively delegate to itself. |
| T02 | supported: Thin wrapper loads the discovered documentation skill and relevant references. |
| T03 | supported: Discloses missing guidance/source rather than claiming access. |
| T04 | supported: Returns useful content/findings, checks and uncertainty. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Assigned docs/examples only; review mode is read-only; product edits need assignment. |
| G01–G04 | supported where applicable: Inherits caller model/tools/permissions; no duplicated specialist method. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Exercise the final documentation skill through native role dispatch on fresh reader/review tasks and missing-resource cases; the observed role run preceded the final example.

### `agents/copilot/documentation-agent.agent.md`

SHA-256: `8b967322685529368bd5f3da01afb7ee7f8840a30288f88dc571f741280c3e13`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Copilot documentation delegation, including review-only requests. |
| T02 | supported: Loads the discovered shared skill; tools retain original host configuration. |
| T03 | supported in revised source: explicit file read, exact fallback and attempted-path/error disclosure. Four earlier attempts failed; two final cases demonstrated loading, task-source isolation and schema precision without establishing general reliability. |
| T04 | supported: Useful content, significant findings, actual checks and gaps. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Review-only leaves files unchanged; source instructions do not grant authority. |
| G01–G04 | supported where applicable: Thin host adapter, existing tool list preserved. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Repeat fresh sparse-contract and missing-resource cases under ordinary host routing; two final passes do not establish reliability or all error paths.

## Observed behavior and remaining limits

The [sanitized observations](observations.json) retain all failures, settings and exact
resource identities. The initial documentation comparison passed eight expectations per
arm on three public cases, before the final grounding example. Only Pulse was repeated
against the final skill: both arms passed three expectations. Earlier Roster/translation
results therefore remain prior-runtime evidence. Actual Codex documentation-role dispatch,
skill reading and an executed README example were independently observed on the earlier
skill snapshot; they do not establish the final example's behavior through that role.

Copilot exposed four failed development attempts: omitted skill loading, substitution of
installed evaluation fixtures for task evidence, and two repetitions of unsupported API
field/state inference. A different DELETE scenario passed before the final change, but it
did not cancel those failures. The corrections made actual loading and task-source boundaries
explicit and added one general schema-precision example to the shared skill.

Independent inspection confirmed that the two final-runtime Copilot cases (original sparse
jobs scenario and different DELETE scenario) selected the actual role, read the skill once,
avoided evaluation-fixture reads and unsupported details, and preserved files. They used
Copilot CLI `1.0.89-4` with `claude-sonnet-5`/medium explicitly pinned to the initially
observed host defaults, and existing authentication transiently in a secret-marked
environment variable. Tools/model settings were not changed
by the migration. Successful exit alone was never used as the outcome oracle.

The repeated original prompt is a development case, not held-out validation. The separate
scenario provides only a narrow transfer check. Review-only file preservation was observed;
missing-resource behavior, normal routing reliability, browser accessibility, other model
combinations and real-reader success remain open checks. Verdict remains `ready_with_limits`.
