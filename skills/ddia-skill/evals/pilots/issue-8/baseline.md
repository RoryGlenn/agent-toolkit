# A. Keep the export script

Keep PostgreSQL and the cron job. The supplied load, latency, and export duration show no capacity problem. Duplicate exports have negligible cost, so Kafka, a workflow service, and distributed locks add operational obligations without an established benefit, especially for a two-person team unfamiliar with them.

Spend the sprint on specific gaps: visible last-success time, failure alerts, bounded retries, execution logs, and a documented rerun procedure. Generate to a temporary artifact and publish atomically if readers could otherwise receive incomplete CSVs. Establish whether exports need a consistent database snapshot; use one if that is the actual requirement. Add overlap prevention only if concurrent executions cause meaningful load or publication errors.

A concrete possible failure is: the process writes half a CSV, crashes, and a consumer reads the partial file. Another is a missed cron execution remaining unnoticed. Neither is established as currently occurring. Duplicate execution alone is not a consequential failure on the stated facts.

Unknowns include export freshness expectations, delivery commitments, concurrent export demand, consumer behavior, and recovery expectations. Existing backups do not establish successful restoration. Verify with representative exports, a restore exercise, and process termination before and after publication; confirm alerts, reruns, and reader behavior.

Reconsider the architecture if measured workloads exceed capacity, missed work must survive long outages, many dependent stages need durable retries, or exports trigger consequential external effects. Specify those requirements and evaluate a database-backed job queue or a managed workflow service first. Kafka becomes plausible when durable event distribution and independent consumers are needed; it is not a general production-readiness prerequisite.

# B. Resolve the partition requirement

Clarify whether “accept reservations” means immediately confirm a seat or acknowledge a pending request. Pending acceptance can satisfy the literal requirements. Immediate confirmation in both disconnected regions cannot coexist with the no-oversell guarantee for one unallocated seat.

The failure trace is straightforward: both regional databases show one seat; the link fails; each region confirms a different customer. Two customers now have a confirmed claim on one seat. Last-write-wins can discard one database record afterward, but cannot make the earlier confirmation cease to have happened. If acceptance remains pending, merging still needs an explicit allocation decision and durable records of both requests, rather than silently losing one.

Quorum writes require intersecting participants to establish a common order. A partition prevents every disconnected region from independently obtaining that coordination. A distributed lock has the same limitation: independent grants violate exclusion; refusing grants sacrifices availability. Fencing protects against stale holders only when the authoritative inventory update enforces it.

Realistic choices are:

- Preserve confirmation safety: use one authoritative allocation decision, and let regions unable to reach it reject, queue, or return pending status.
- Accept requests locally as pending; confirm at most one after coordination becomes possible. Product must approve the pending semantics and customer experience.
- Preallocate exclusive inventory rights. A region can confirm within its rights during a partition, but the single remaining seat belongs to at most one region. This changes the supplied design and still cannot guarantee confirmation everywhere.
- Permit overselling and compensation, explicitly changing the safety requirement.

No implementation can remove that tradeoff. Verify the selected contract using simultaneous last-seat requests during partitions, delayed messages, failover, and stale lock-holder attempts. Assert both inventory invariants and the externally visible confirmation history, not just the reconciled database count. Availability duration and latency expectations remain unspecified.

# C. Make billing reproducible and publication idempotent

The proposed job can misbill and duplicate charges. A measurement from before a price increase receives today’s tariff; a measurement arriving two hours late is dropped despite the supported 48-hour lateness; a 30-day-old replay passes expired dedupe state and can append another charge unless sink uniqueness is actually used.

Retain replayable measurement inputs and tariff history. Join each measurement to the tariff for its tenant/device class whose effective interval contains its event timestamp. Define timestamp boundaries, missing tariffs, overlapping updates, and retroactive tariff corrections. A compacted table retaining only the latest value per tenant/class cannot provide that history; versioned keys plus retained history can. Preserve the tariff preceding the replay window as well.

Use a lateness allowance covering 48 hours, with an explicit route for later or invalid events. Watermarks may finalize provisional results; they should not silently discard billable measurements. Preserve event identity as `(tenant, event ID)` and detect conflicting payloads under the same identity.

Write idempotently using the sink’s `(tenant, event ID, calculation version)` uniqueness constraint, including across replay and checkpoint recovery. Retain dedupe state for the replay horizon if correctness depends on it; durable sink uniqueness can make shorter processing-state retention safe. Acknowledge source progress only after durable writes, and test crash recovery. Uniqueness alone does not prevent missing charges.

For recalculation, define an immutable version identifying code, tariff inputs, and calculation rules. Recompute the affected interval into staging using an explicit input cutoff. Reconcile event coverage and charge differences, then atomically activate the replacement version for that interval. Readers must select the active version rather than sum all versions. Coordinate late arrivals and concurrent processing across activation so coverage has no gaps or duplicates. Already issued bills may need linked adjustments rather than replacement; that is an accounting/product decision.

Verify tariff-boundary cases, 48-hour arrivals, 90-day replay, conflicting duplicates, crash-after-write, concurrent replay/live ingestion, and publication failure. Check event coverage and amounts against an independent fixture. Input retention and previously settled billing behavior remain unknown.

# D. Delete across serving and recovery paths

“Not authoritative” does not mean harmless: deleted content can still appear in search, vector retrieval, training datasets, or a restored system. A concrete resurrection trace is: delete the current row, restore last month’s database, then rebuild indexes from an archive containing the message. The message becomes accessible again.

Create a durable deletion registry, independent of database rollback, recording the minimum identifiers and scope needed to suppress resurrection. Make deletion a tracked, retryable operation: remove authoritative content, block serving while asynchronous removals catch up, delete search/vector entries, and locate derived dataset copies through lineage. Ensure ingestion, index rebuilds, and in-flight workers consult deletion state so delayed work cannot reinsert content. Record completion per destination and retry failures.

For immutable archives and backups, first establish the required deletion and retention policy. Options include expiring or rewriting eligible archives, filtering every replay, or cryptographic erasure where independently disposable keys genuinely cover all recoverable copies. Access restrictions alone are not erasure. State clearly which retained copies remain and when they expire. Retain suppression information for as long as any recoverable source can reintroduce the content.

Recovery must obtain the current deletion registry, apply all applicable deletions to restored rows, filter archived events during rebuild, and verify derived stores before enabling service. Do not restore the registry to the backup’s older state. Use the full applicable registry, since archives may contain data older than the restored snapshot.

Inventory training datasets and remove or rebuild affected examples as policy requires. Removing examples does not establish that previously trained models have forgotten them; model retraining, unlearning, and use restrictions need separate decisions and validation.

Policy must define deletion scope, deadlines, exceptions, backup/archive retention, audit evidence, and treatment of trained models. No jurisdiction or policy is supplied, so this plan makes no legal-compliance claim. Verify with seeded messages, delayed indexing, replay, and an isolated month-old restore; test both direct reads and retrieval, including failures and retries.
