# Topic routing and coverage

The machine-readable [coverage ledger](coverage.json) links concept clusters to source
sections, procedures and evaluation cases. `scripts/guide.py route QUERY` ranks routes
without requiring the private source library. Load only selected sections of chapter
references. `guide.py topics --chapter N` lists all concept clusters in a chapter.

Coverage means authored practical guidance, not demonstrated agent competence. A case
being linked or an anchor resolving does not establish conceptual fidelity or a passing
behavior evaluation. The suite records these evidence types separately.

| Chapter | Reference | Concept clusters |
| --- | --- | --- |
| 1 | [Chapter 1](chapters/01.md) | `workload-separation`, `authority-derived`, `cloud-operations`, `distribution-necessity`, `service-boundaries` |
| 2 | [Chapter 2](chapters/02.md) | `load-shape`, `performance-objectives`, `overload`, `reliability-recovery`, `maintainability` |
| 3 | [Chapter 3](chapters/03.md) | `aggregate-models`, `denormalization`, `graph-queries`, `event-models`, `analytical-shapes` |
| 4 | [Chapter 4](chapters/04.md) | `storage-engines`, `indexes`, `columnar`, `search-indexes`, `vector-search` |
| 5 | [Chapter 5](chapters/05.md) | `compatibility`, `encoding-types`, `schema-formats`, `rpc-outcomes`, `durable-workflows` |
| 6 | [Chapter 6](chapters/06.md) | `replication-durability`, `replication-reads`, `multi-leader-sync`, `conflict-resolution`, `leaderless-quorums` |
| 7 | [Chapter 7](chapters/07.md) | `sharding-need`, `shard-keys`, `hotspots`, `rebalancing`, `distributed-indexes` |
| 8 | [Chapter 8](chapters/08.md) | `transaction-boundaries`, `isolation-anomalies`, `write-skew`, `distributed-transactions`, `message-atomicity` |
| 9 | [Chapter 9](chapters/09.md) | `ambiguous-failure`, `clock-assumptions`, `leases-fencing`, `failure-models`, `formal-testing` |
| 10 | [Chapter 10](chapters/10.md) | `consistency-contracts`, `partition-tradeoffs`, `logical-identities`, `consensus-mechanisms`, `coordination-use` |
| 11 | [Chapter 11](chapters/11.md) | `batch-baseline`, `batch-storage`, `batch-orchestration`, `batch-dataflow`, `derived-publication` |
| 12 | [Chapter 12](chapters/12.md) | `stream-delivery`, `cdc-handoff`, `stream-history`, `stream-time-joins`, `stream-recovery` |
| 13 | [Chapter 13](chapters/13.md) | `derived-dag`, `reprocessing-evolution`, `dataflow-clients`, `end-to-end-identity`, `integrity-audit` |
| 14 | [Chapter 14](chapters/14.md) | `human-purpose`, `bias-feedback`, `accountability`, `privacy-lifecycle`, `law-society` |

## Cross-cutting routes

- Retry/replay/external effects: rpc-outcomes, durable-workflows, message-atomicity,
  stream-recovery, end-to-end-identity, integrity-audit.
- Scarce shared resources: isolation-anomalies, write-skew, consistency-contracts,
  partition-tradeoffs, conflict-resolution, distributed-indexes.
- A new platform/component: distribution-necessity, cloud-operations, service-boundaries,
  workload-separation, maintainability; add workload-specific storage/model topics.
- Data evolution: compatibility, schema-formats, reprocessing-evolution, cdc-handoff,
  batch-storage, privacy-lifecycle.
- Failure and recovery: reliability-recovery, ambiguous-failure, clock-assumptions,
  leases-fencing, failure-models, formal-testing, stream-recovery.

## Source limits

The canonical map is DDIA Second Edition. First-edition chapter numbers differ; route
by topic, then verify the actual edition and section. References are original syntheses
and applied procedures; they are not a substitute for the book or every cited paper.
Existing text-reading records did not visually interpret every diagram, execute all book
code, or verify external bibliographies. Inspect layout-sensitive source when it matters.
Chapter 13 presents a philosophy, not a universal instruction to unbundle databases.
