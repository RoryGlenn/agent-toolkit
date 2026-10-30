**A. Keep PostgreSQL and the export cron.** The supplied workload meets its latency target with substantial headroom; duplicate read-only exports have negligible cost. Three unfamiliar services introduce deployment, recovery, monitoring, and coordination work without a demonstrated requirement. Nothing supplied establishes an existing correctness defect.

Spend the sprint on a bounded export timeout, failure alerts, last-success visibility, a short rerun/recovery runbook, and an exercised database restore. Generate to a temporary artifact and publish only after success so consumers cannot mistake a partial CSV for a completed export. Define whether an export needs a consistent database snapshot; use an appropriate read transaction if it does. Retrying after an uncertain completion may generate a duplicate, which is explicitly acceptable here. A distributed lock is unnecessary for that consequence; add overlap suppression only if measurements show overlap causes harm.

Facts that could change this decision include an export completion/freshness deadline the script cannot meet, sustained database contention, many independent consumers requiring replay, costly or irreversible export side effects, or long-running multi-step jobs requiring durable recovery. First measure duration, failures, resource use, and missed deadlines. A PostgreSQL-backed job table is a smaller alternative when durable status/retries become necessary. Kafka or a workflow service would need a specific capability and an owner able to operate it; growth alone does not justify all three components.

Verify by killing the exporter mid-write, rerunning it twice, and checking that only complete artifacts are published, failures alert, and app latency remains within target during exports. Restore a backup and run an export from it.

Book grounding: DDIA 2e, chapter 2, “Simplicity: Managing Complexity,” `OEBPS/ch02.html#id38`, connects complexity to maintenance and bug risk. The implementation choices above are applied reasoning from the supplied workload, not current product guarantees.

**B. The requirements cannot all hold for confirmed reservations.** During a partition, both regions see one available seat. Region A confirms Alice; independently, B confirms Bob. Neither can distinguish this execution from one where it receives the only request. Last-write-wins later retaining Alice's row cannot undo Bob's confirmation: the business invariant was already violated.

Globally intersecting quorums can provide coordination only by making a disconnected side unable to obtain the required quorum. Independent regional quorums can both succeed and do not solve the shared-seat problem. A globally exclusive lock has the same availability boundary; locks independently granted on both sides cease to be exclusive. Lock leases also need safe handling of stale holders, but even perfect exclusion cannot permit both isolated regions to confirm the last seat.

Realistic choices require a product decision:

- Preserve no overselling: serialize seat allocation through an authoritative coordinator and atomic inventory check/reservation. A region unable to reach that authority must reject, wait, or return a clearly unconfirmed pending request. Use request IDs for uncertain outcomes and retries.
- Preserve immediate local acceptance: accept requests as pending and resolve them after coordination, or explicitly permit overselling and compensation. A pending acknowledgment must not promise a confirmed seat.
- Preallocate exclusive inventory rights: confirm locally only while a region has rights. Transfers need coordination; with one remaining seat, at most one region owns its right. This changes the stated setup and still cannot promise confirmation everywhere.

Topology, latency budgets, and which degraded behavior customers accept remain unknown. No named database or lock product guarantee is assumed.

Verify with a partition test issuing simultaneous requests in both regions; record external confirmations, not merely final merged rows. For the coordinated design, assert at most one confirmation, then test timeout/retry and failover without duplicate allocation.

Book grounding: chapter 10, “The CAP theorem,” `OEBPS/ch10.html#sec_consistency_cap`, explains the coordination/partition availability boundary. The seat interleaving and rights alternatives are applied reasoning.

**C. Replace the latest-value join and append-only billing path.** A measurement at 10:00 arriving after an 11:00 tariff change is billed at the wrong rate by a latest-value join. A two-hour delay is valid under the supplied 48-hour lateness but is dropped. A 90-day replay outlives seven-day dedupe markers. However, atomic sink uniqueness on tenant/event/calculation-version can still prevent duplicate rows within one version; marker expiry alone does not prove duplicate charges there.

Retain measurements and tariff history sufficient for the replay horizon, including the tariff effective before its earliest timestamp. Join each measurement to the greatest effective timestamp no later than its event timestamp, within tenant/device class. Define equal-timestamp conflicts, missing tariffs, timestamp validity, and tariff corrections. Compaction keyed only by tenant/class loses required versions; keys including effective timestamp may retain them, depending on actual retention settings.

Accept the full 48-hour lateness, with corrections or delayed finalization; a watermark is not proof that older events cannot arrive. Route exceptional arrivals for explicit reconciliation. Keep durable dedupe at the sink throughout every supported retry/replay interval, and atomically enforce uniqueness with the charge write. Persist accepted output before acknowledging input; crash-after-write retries must hit the same identity. Detect conflicting payloads for one event ID.

Recalculate into an isolated calculation-version using pinned input boundaries, tariff history, code, and rounding rules. Validate completeness, totals, temporal-boundary samples, and differences against the prior version. Catch up concurrent/late inputs through an explicit cutover boundary, then atomically publish an active-version manifest for the billing scope. Readers must select that version rather than sum every appended version. Retain rollback metadata. Already issued charges require auditable, idempotent adjustments or reversals; publishing a new version must not charge everything again.

Verify 48-hour lateness, tariff-boundary events, a 90-day duplicate replay, concurrent live/replay processing, and crashes before/after sink commit and publication.

Book grounding: chapter 12, “Time dependence of joins,” `OEBPS/ch12.html#sec_stream_join_time`; “Handling straggler events,” `#id343`; “Idempotence,” `#sec_stream_idempotence`. These support temporal history, corrections, and retry reasoning; the publication design is an applied deduction.

**D. Deletion must cover every retrievable copy and its recovery path.** Deleting the authoritative row leaves searchable text, vectors, and training examples accessible. Restoring a month-old database can restore the row; rebuilding from an unfiltered archive can resurrect deleted messages in indexes even if the restored row is absent. “Derived” does not mean inaccessible or harmless.

Define the deletion scope and stable identifiers, then atomically remove/mark authoritative data and record a durable deletion instruction. Maintain a deletion ledger outside the database's rollback boundary; preserve it longer than any source capable of resurrecting data. Use a transactional outbox or equivalent reliable handoff, idempotent consumers, and per-store acknowledgments. Block serving deleted content immediately through an authoritative suppression check while asynchronous purges complete; account for outages and caches in that path.

Purge search/vector entries and regenerate or filter affected training datasets using lineage. Inventory exports, intermediate copies, and any downstream artifacts within scope. Record completion evidence without retaining deleted message contents. Reconcile stores periodically to catch missed events.

For archives, choose supported excision/rewrite or a prospective encryption design with suitably granular keys and deletion of every usable key copy. A tombstone alone does not erase archived bytes. Backups need explicit retention/access rules and deletion on expiration, or a supported selective removal mechanism. Do not call suppression physical erasure.

Restore into quarantine. Apply the current deletion ledger to restored rows, filter archive replay, rebuild every derived store, reconcile acknowledgments, and verify absence before reopening access. Protect the ledger itself against rollback and loss.

Policy must decide deletion deadlines, scope, exceptions/holds, archive and backup retention, acceptable interim inaccessibility, and treatment of previously generated training artifacts. No jurisdiction or policy was supplied, so this is an engineering plan, not a compliance conclusion.

Verify with a canary message deleted after the chosen backup: restore that backup and replay archives, then probe database, search, vector retrieval, datasets, and serving paths. Repeat with delayed/retried deletion consumers.

Book grounding: chapter 12, “Limitations of immutability,” `OEBPS/ch12.html#sec_stream_immutability_limitations`, discusses persistent copies, excision, and crypto-shredding limitations. The ledger and restore protocol are applied reasoning.
