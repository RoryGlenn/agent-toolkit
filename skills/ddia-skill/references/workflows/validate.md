# DDIA Validate procedure

Read [the common decision process](../decision-process.md), then only relevant [topic routes](../routing.md).

Translate the business requirement into an observable invariant and a test oracle independent of the implementation. Specify what would falsify the claim. Include a correct control and a deliberately broken variant when this demonstrates oracle sensitivity.

Choose evidence appropriate to the claim. A deterministic schedule can expose a conceptual failure; SQLite can establish SQLite behavior; PostgreSQL isolation needs the actual supported PostgreSQL configuration. A process exception does not stand in for power loss, and a model is not production code.

Control the critical schedule using barriers or explicit state transitions rather than timing sleeps when feasible. Include commit/ack boundaries, delayed responses, process restarts, duplicate identities, payload mismatch and retention/replay where relevant. For overload, test recovery after demand falls. For migrations, test mixed versions and rollback.

Record commands, versions/configuration, seed/schedule, observed effects, invariant result and limits. Preserve the counterexample artifact. Do not call a seeded random test deterministic simulation unless clock, I/O, network and scheduling nondeterminism are actually controlled.

The bundled experiments illustrate bounded mechanisms and broken/correct controls. They do not certify the caller project. Reuse their invariants only when the actual business semantics match.
