# DDIA Migrate procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Inventory active readers/writers, stored history, in-flight workflows, client versions and derived copies. State the invariant maintained throughout the migration, not only the desired final schema. Build a writer-reader compatibility matrix including rollback and old read-modify-write behavior.

Choose a staged transition such as expand, compatible writes, backfill/catch-up, compare, cut over, retire. Tailor this to the engine and protocol; it is not a universal ordering rule. Use versioned inputs and derivation code for reprocessing. Keep replayed computation separate from irreversible external effects.

Define backfill identity, resumability, progress, rate limits and interaction with concurrent changes. Establish snapshot/log boundaries for CDC and shard transfer. Reject stale ownership at the protected resource where required. Budget capacity for both versions and recovery.

Describe the exact commit point, rollback before/after it, handling of partially converted rows and operator stop conditions. Identify when rollback requires data transformation rather than merely old code.

Validate mixed old/new versions, retry after interrupted backfill, delayed changes, historical enrichment, deletion propagation and readers during cutover. Publish compatibility and recovery evidence to the existing project decision/handoff system.
