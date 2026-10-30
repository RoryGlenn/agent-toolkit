# DDIA Assess procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Establish the user-visible consequence of omission, duplicate execution, staleness or delay. Inspect the existing database, runner and provider guarantees before proposing machinery. Compare the current design, the smallest sufficient correction and a meaningful more capable option.

Trace at least the consequential failure the proposed mechanism addresses. Separate credible workload/failure evidence from speculative scale. Ask only for facts that could reverse the decision; otherwise state bounded assumptions. An acceptable recommendation can be no change, an index, a constraint, or a simpler job.

For every added queue, cache, replica or coordinator, identify the unmet requirement, why a simpler option fails, operating burden, recovery owner and removal/revisit trigger. Do not make reliability machinery mandatory for harmless repeatable operations.

Return a recommendation, protected requirement, dominant tradeoff, evidence, uncertainty and next falsifying experiment. A verdict should not depend on whether the design resembles a favorite pattern.

For retry/deduplication specifically, distinguish the original business intent from a transport attempt. Check request identity, payload reuse, provider retention, timeout-after-commit and operational replay. A local dedupe table alone cannot establish remote exactly-once effects.
