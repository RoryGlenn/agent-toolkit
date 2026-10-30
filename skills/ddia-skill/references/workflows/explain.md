# DDIA Explain procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Start with the question the concept helps answer, using the current project or an explicitly invented small example. Identify the relevant requirement and one incorrect execution before introducing terminology. Match detail to the reader.

Retrieve the original section before attributing a consequential claim to the book. Separate book principle, applied deduction and current product behavior. Inspect original figures/tables when their layout matters; text extraction alone does not establish their interpretation.

Show a correct design and its limitations alongside the failure. Distinguish frequently confused concepts: durability versus replication, isolation versus consistency, 2PL versus 2PC, logical order versus wall time, convergence versus invariant preservation, and framework-internal versus end-to-end exactly-once.

Use a small runnable experiment or operation history when it clarifies the causal mechanism. State its scope: a simulated lease schedule is not a distributed resource implementation, and an SQLite transaction does not prove PostgreSQL behavior.

Conclude the explanation with the actual decision criteria or a falsification exercise, not a technology prescription. If source retrieval is unavailable, disclose that and teach from general expertise without fabricated book citations.
