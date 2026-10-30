# Software-design adoption assessment

Date: 2026-10-30. Assessor: implementation agent (source assessment, not independent execution).
Base revision: `156ca63e5bbc1a76205c24d919a3d9b4d3c13d36`.
Exact entrypoint SHA-256 values are recorded below and in the [adoption inventory](../adoption.json).
The [resource manifest](runtime-sha256.json) binds non-evaluation skill package resources,
including optional documentation tooling, and all seven roles; generated caches are excluded.
Entrypoint hashes alone do not bind those supporting resources.

## Intended value and applicable profiles

Apply explicit caller-cost and information-hiding reasoning with retrievable source qualifications. These procedures offer a reusable decision method; no advantage over baseline is inferred from the assessment.

Book/reference specialist and Codex host adapter.

## Findings and corrections

No runtime prose change was necessary. Existing instructions already cover invocation, meaningful alternatives, source qualification, ownership, useful findings and proportionate scope. Added a runnable three-case set and assessment; no heading normalization or duplicate method was introduced.

## Evidence and disposition

Existing source-retrieval tests and RecordBatch design tasks remain available. New cases cover a lifecycle-heavy API, an adjacent wording request and a sufficient small helper without an original source library. A passing retrieval test is not a design-quality result.

The semantic assessments below mean the authored contract is supported by inspected content.
Runtime selection, effective host permissions, outcome reliability and comparative value remain
unverified except where a separate observed receipt explicitly records them. T05 is supported
as an authored case/evaluation-gap record, not as passing model behavior. Scoped live results and exact
executed repository checks are recorded in the [shared evidence record](evidence.md)
and [sanitized observations](observations.json).

Verdict for each artifact: **ready_with_limits**. No required source-contract gap remains in
this assessment; independent review and unavailable execution checks retain their own scope.

## Individual assessments

### `skills/software-design-skill/SKILL.md`

SHA-256: `28d816684bb30417fe31077bbdd947ac96fc83e9b6be199cd6387ca6caab7b38`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Consequential module/API/maintenance decisions; routine edits need no consultation. |
| T02 | supported: Trace representative caller/change; compare semantic contracts and hidden knowledge. |
| T03 | supported: Retrieve original sections before attribution; distinguish book principle, repository evidence and deduction; disclose missing source. |
| T04 | supported: Concrete finding/decision, burden removed, remaining complexity and verification. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Consultation read-only; implementation only with sole ownership; no recursive specialist delegation. |
| G01–G04 | supported where applicable: Conditional retrieval, no quotas or blanket pattern bans. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Run lifecycle API and correct-helper controls; inspect caller-cost analysis independently.

### `agents/codex/software-design-agent.toml`

SHA-256: `3a244f8af8dd82e6ae71056ddf82d6916cb146fffebd7b553cb51fc764f960bb`.

| Requirement | Assessment and evidence |
| --- | --- |
| T01 | supported: Separate design consultation with task and constraints. |
| T02 | supported: Thin wrapper loads the actual discovered skill and relative resources. |
| T03 | supported: Discloses missing material; preserves source versus deduction distinction. |
| T04 | supported: Decision/findings, supporting evidence, actual checks and uncertainty. |
| T05 | supported: representative cases and explicit execution gaps are linked above; scoped live outcomes and remaining gaps are recorded in the shared evidence receipt. |
| T06 | supported: Advises designated writer; edits only under sole ownership; no recursion. |
| G01–G04 | supported where applicable: Inherits caller settings and avoids duplicating the skill. G04 applies to wrappers; for skills it is not applicable. |

Next meaningful check: Extend observed role dispatch/fallback with held-out caller-cost cases and successful supplied-source reads; verify normal routing.

## Observed scope

Native Codex integration independently demonstrated actual software-design role dispatch,
its own skill read and honest missing-source fallback on one small integer-contract task.
That is not a paired design-quality comparison or successful original-book retrieval. The
three authored design-specific cases remain available for a fresh controlled campaign.
See [evidence](evidence.md) and [observations](observations.json) for identities and limits.
