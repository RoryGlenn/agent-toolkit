# Artifact review record

Use this record for a consequential new package or a substantive revision. Scale the
evidence to the task. This is a reviewer worksheet, not instructions loaded into every
runtime skill. A small edit does not require rerunning an unrelated benchmark.

## Identity and intended value

- Artifact path and exact Git revision or content hash:
- Reviewer and date:
- User outcome and representative task:
- Target host/version and relevant environment:
- Why existing model knowledge or another package is insufficient:

## Semantic review

| Check | Evidence to inspect | Assessment |
| --- | --- | --- |
| T01: job and routing | Natural request that should activate it; nearby request that should not | Pending |
| T02: useful expertise | Specific procedure, domain constraint, or example that changes the result | Pending |
| T03: grounding | Original source or observable repository behavior; qualifications preserved | Pending |
| T04: output and completion | A result the caller can use and the checks that support it | Pending |
| T05: evaluation | Actual artifacts and traces; exceptions and evidence gaps | Pending |
| T06: ownership | Handoff, assigned write scope, and observed role behavior if applicable | Pending |
| G01-G04: efficiency | Relevant reads, proportionate process, justified scripts and wrappers | Pending |

Use `supported`, `needs_change`, `unverified`, or `not_applicable`, with a short reason.
Do not infer successful behavior from headings, preferred words, checklist completion,
file counts, or a second model agreeing with the author's explanation.

## Behavior evidence

Record the cases actually run, exact commands or actor prompts, immutable inputs/output
locations, outcomes, failures, and remaining limits. Separate:

- Package/format validation.
- Trusted fixture or helper tests.
- Explicitly invoked skill behavior.
- Normal discovery/routing and actual named-role execution.
- Paired comparison against a baseline or previous revision.
- Real user outcomes, when available.

For comparisons, specify the intervention and hold model, task, tools, environment, source
availability, effort, and budgets constant where the claim requires it. Keep expected
answers and hidden tests unavailable to actors. Retain failed runs and report the number
of independent cases and repetitions. A single success is smoke evidence, not reliability.
Where a model judge is useful, retain the rubric and artifact evidence; do not present its
agreement as external community approval or replace objective oracles with prose scoring.

## Disposition

- Actionable findings and corrections:
- Accepted local tradeoffs:
- Unrun checks and why:
- Next check that could materially change confidence:
- Verdict: `needs_review`, `ready_with_limits`, or `needs_change`:

Link a completed record as `review_record` and change the adoption entry's assessment to
`reviewed`. That label records that review occurred; the completed record carries the actual
verdict and limits. The checker verifies the link exists, not the truth of the assessment.
