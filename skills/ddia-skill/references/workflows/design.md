# DDIA Design procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Map authoritative facts, derived representations and read/write paths before choosing products. Identify business invariants, transaction scope, consistency/freshness needs, peak/skewed workload and operator capacity. Use the data-contract asset only if the project lacks a suitable existing document.

Compare a simple baseline with a meaningful alternative. Evaluate query/model fit, capacity, availability, evolution, recovery, ownership, cost and human consequences relevant to this project. Describe how the choice changes if the dominant assumption fails. Avoid a catalog of unrelated technologies.

Trace one realistic concurrent operation and one partial failure across data boundaries. Explain where ordering, uniqueness, durable identity and reconciliation are actually enforced. Check current official product/version documentation for guarantees that affect the decision.

Record the chosen option in the existing decision system or decision asset: requirements, alternatives, evidence, rejected complexity, consequences, rollout/rollback and measurable revisit trigger. Export concrete constraints and test obligations to the implementation owner; preserve product/business authority when tradeoffs require it.

For project creation, resolve current needs first. Do not generate global rules such as always use an outbox or always retry three times. Associate each constraint with its scope, invariant and evidence.
