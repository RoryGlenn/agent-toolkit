# DDIA Operate procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Map user operations to measurable service objectives, authoritative/derived state and dependency ownership. Choose useful metrics for tails, errors, admission, lag, recoverable retention, saturation and reconciliation discrepancies. Avoid monitoring that cannot drive an action.

Define tolerated faults and separate data-loss objectives from restoration time. Include correlated bad deployment/configuration and accidental deletion. Confirm independent recoverable history; replication alone does not demonstrate backups. Restore into an isolated target and verify business invariants before reopening service.

For overload, inspect queue and pool bounds, deadlines, cancellations, retry budgets, shedding/backpressure and recovery behavior. For storage, include compaction, index builds, disk headroom and rebalancing. For streams, monitor remaining replay horizon rather than offset lag alone.

Write actionable operator steps, prerequisites, ownership, expected observations, stop/escalation conditions and repair/reconciliation. Treat ambiguous external outcomes as unknown until evidence resolves them; do not blindly retry irreversible work.

Report demonstrated recovery time/data gap, not a promised objective inferred from a healthy backup job. Include retention/deletion through backups, exports, derived stores and offline clients, with current legal requirements checked separately where needed.
