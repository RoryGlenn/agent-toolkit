# DDIA Review procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Read the original requirement and exact affected execution paths. Reconstruct source-of-truth, transaction, identity, ordering and recovery boundaries from code/configuration. Load relevant concepts, including privacy and operational costs when the change affects them.

For each possible defect, construct a reachable interleaving, failure window, incompatible rollout or workload counterexample. Cite file/line and the assumption needed to reach it. Distinguish a reproduced violation, static evidence and an unresolved deployment question. Confirmed findings must connect to an actual requirement.

Recognize correct controls. Snapshot isolation is not automatically serializable, but do not flag a protected operation simply because stronger isolation exists. A missing component is not itself a defect. Check whether simpler constraints or existing guarantees suffice.

Review proposed AGENTS/skill rules as executable advice: unconditional retries, lock-before-write, dedupe cleanup-after-ack and blanket distribution may encode invalid assumptions. Recommend scoped rules with business invariant, mechanism and verification instead.

Return consequential findings first, each with impact, trigger, proportional remedy and verification. If no issues are found, state inspected boundaries and material uncertainty. Consultation is read-only; return findings to the designated writer.
