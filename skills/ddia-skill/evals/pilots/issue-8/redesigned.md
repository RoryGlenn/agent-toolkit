### A. Keep the existing export job

Do not build Kafka, a workflow service, or Redis locks next sprint. The supplied workload meets its latency target with substantial headroom; a 20-second read-only export and harmless duplicate execution establish no need for distributed coordination. Two operators learning three systems would gain dependencies and recovery work without an identified benefit.

Keep PostgreSQL and cron. Add only missing basics: recorded last successful export, duration/error reporting, an alert when an export is overdue, bounded retry, and a short rerun procedure. If users consume files during generation, publish a completed temporary file atomically using the destination's supported mechanism. Establish whether each CSV needs a consistent database snapshot before selecting transaction behavior.

Concrete trace: the job publishes the CSV, then crashes before recording success. A retry generates it again. Given the stated cost and read-only behavior, that is acceptable; a distributed lock does not need to prevent it. Conversely, a crashed cron host may miss the run: alerting and rerunning address that failure if the export deadline permits.

Unknowns that could change the decision are export freshness/recovery objectives, missed-run consequences, measured interference with API traffic, substantial future load, multiple independent consumers needing retained replay, or a genuinely long-running multistep process with consequential effects. First consider query tuning, scheduling changes, or a PostgreSQL-backed job record; adopt a new service only when those fail a demonstrated requirement and someone owns its operation.

Verify by killing the job before and after publication, rerunning it, checking CSV completeness and overdue alerts, and measuring API latency during export. A successful backup job alone does not demonstrate restoration; conduct a restore drill against an agreed recovery objective.

Source principle: DDIA 2e, “Problems with Distributed Systems,” `OEBPS/ch01.html#sec_introduction_dist_sys_problems`. The component decision above is applied reasoning from the supplied facts.

### B. The requirements conflict

Immediate confirmed reservations in both isolated regions, no overselling, and no preallocated rights cannot all hold for the last seat. This is a business-invariant conflict, not a missing implementation technique.

Trace: both databases show one seat. Partition the regions. Region A confirms Alice; region B, unable to distinguish this history from one where A received no request, confirms Bob. Two confirmations now exist. Last-write-wins may later erase one booking, but cannot undo the already issued confirmation or satisfy “ever.” Separate booking rows can also survive merging while overselling the resource.

A correctly shared coordination service or intersecting quorum cannot allow both disconnected sides to independently authorize the same final unit. Some requests must wait or fail. Independent regional quorums/locks do not provide global exclusion. A globally safe lock service has the same partition tradeoff; leases also require the protected storage to reject stale holders. Merely adding a lock name proves nothing.

Realistic product choices are:

- Preserve confirmations: designate an authority per seat, or use a coordinated conditional reservation. During partition, regions lacking authority must reject, wait, or route to an authority they can reach.
- Accept requests everywhere as explicitly pending, confirming only after coordination. This changes immediate reservation semantics.
- Preallocate exclusive inventory rights and coordinate transfers. A region can confirm only while it owns unused rights; the last seat can belong to at most one region. This still cannot guarantee successful confirmation in both regions for that seat.
- Allow overselling and compensation only if product explicitly relaxes the invariant. Refunds do not preserve the original requirement.

Verify the chosen contract by partitioning regions and submitting competing requests, including retries, lost acknowledgments, failover, and stale lock holders. Assert against the history of confirmations, not merely the converged seat count. The engineer's proposed quorum protocol and failure assumptions remain unspecified.

Source principles: DDIA 2e, “The CAP theorem,” `OEBPS/ch10.html#sec_consistency_cap`, and “Dealing with Conflicting Writes,” `OEBPS/ch06.html#sec_replication_write_conflicts`. The reservation counterexample is applied reasoning.

### C. Preserve historical meaning and separate calculation from billing

Reject the proposed pipeline. A measurement at 09:00 under tariff A, delivered after tariff B becomes current, gets B; replay can change it again. A 24-hour-late measurement is valid under the supplied 48-hour bound but is discarded. Seven-day dedupe expiry permits an older replay to be processed again; whether it duplicates a charge depends on durable sink enforcement.

Join by tenant/device class to the tariff interval containing event time: greatest effective timestamp at or before the measurement, with explicit boundary/tie rules. Retain historical tariffs, including the predecessor needed at the replay window's beginning. Latest-only compaction loses required versions. Define handling of missing tariffs, invalid timestamps, delayed tariff updates and retroactive corrections; quarantine unresolved events rather than guess.

Support at least 48 hours' lateness, with sufficient retained inputs/state and a correction path. Replay must bypass inappropriate live watermarks. Retain raw measurements and reference history for the complete 90-day replay plus delivery/recovery margins; establish whether that window is defined by event or arrival time.

Use the supplied sink uniqueness on `(tenant,event,calculation-version)` atomically with each charge write, retaining it across all permitted retries/replays. This is a useful control: durable uniqueness can make seven-day local dedupe merely an optimization. Bind IDs to payloads and flag conflicting reuse. Uniqueness permits different calculation versions; it does not prevent charging both.

Recalculate into an isolated, versioned candidate ledger using pinned inputs, tariff history and code. Reconcile event coverage, per-event amounts and tenant totals; catch up concurrent ingestion through a recorded boundary. Atomically publish an approved version/manifest for the affected interval, so readers never sum old and new versions. Keep rollback available. Already issued invoices/payments need explicit audited delta adjustments, with stable effect IDs and reconciliation; replay must not issue payments directly.

Verify delayed/boundary events, tariff reordering, 90-day replay, duplicate IDs, crashes around sink commit, concurrent catch-up and interrupted publication.

Source principles: DDIA 2e, “Time dependence of joins” (`OEBPS/ch12.html#sec_stream_join_time`), “Handling straggler events” (`OEBPS/ch12.html#id343`), “Uniquely identifying requests” (`OEBPS/ch13.html#id374`), and “Reprocessing data for application evolution” (`OEBPS/ch13.html#sec_future_reprocessing`). Implementation recommendations are applied reasoning; engine guarantees remain unverified.

### D. Delete across copies and prevent resurrection

Deleting authoritative rows alone leaves messages searchable, retrievable through vectors, and available for training. Trace: delete today's row; restore last month's database; replay the immutable archive; the message reappears in rebuilt indexes. “Derived” describes provenance, not accessibility or sensitivity.

Inventory message identifiers and lineage through rows, index documents, vector chunks, archives, datasets, exports/caches and backups. Assign an owner and observable completion state to every copy. Record durable deletion intent atomically with the authoritative change, using an outbox or equivalent recoverable handoff. Acknowledge separately immediate access removal and eventual physical cleanup.

Block deleted messages at every serving path while asynchronous purges complete. Consumers must process deletions idempotently, remove all related chunks/documents, and reject stale inserts/replays using deletion generations or equivalent ordering checks. Reconcile missed notifications. Keep a minimal, protected deletion registry outside rollback to an older backup; retain entries while any older copy can be replayed or restored.

For archives and backups, choose explicit expiry, selective rewriting, or suitably scoped encryption/key destruction where supported. A tombstone prevents reuse but does not erase archived plaintext. Crypto-shredding depends on key granularity and removal of every recoverable key copy. Track pending retention exceptions rather than claiming full erasure. Remove affected training examples and prevent reuse; whether existing trained models require retraining or other remediation is a separate decision, not something dataset deletion proves.

Restore into isolation. Load the current deletion registry before serving or rebuilding, filter archived events, reapply deletions, verify downstream cleanup, and catch concurrent deletion requests through a cutover barrier before reopening access. Do not restore old keys or discard newer deletion intent.

Product, privacy and legal owners must define scope, deadlines, jurisdiction, retention exceptions, backup access/expiry, model obligations and user-facing promises. None are supplied, so this is an engineering plan, not a compliance claim.

Verify with identifiable test messages: delete, inspect every access path, delay/reorder consumers, replay archives and restore old backups; assert no resurrection and audit each copy's status.

Source principle: DDIA 2e, “Limitations of immutability,” `OEBPS/ch12.html#sec_stream_immutability_limitations`. The recovery protocol is applied reasoning.
