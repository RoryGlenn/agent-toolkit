# Curator notes (never staged for actors)

These are original development tasks, not copied book exercises or book prose. Cases apply
principles from the toolkit's three source works:

- **Designing Data-Intensive Applications, second edition:** transaction atomicity and
  isolation; concurrent decisions; separating request/business identity from delivery;
  retry, commit, acknowledgment, retention and replay boundaries; uncertainty around an
  external effect. Our experiments concern SQLite and process exits, not distributed
  transaction or physical power-loss guarantees.
- **A Philosophy of Software Design, second edition:** complete abstractions that hide
  caller obligations; defining avoidable errors out of existence while preserving real
  failures; deep module boundaries; extension costs and knowledge exposed to maintainers.
  Functional tests cannot establish these structural judgments by line or class counts.
- **Docs for Developers, second edition:** audience/task context, working examples,
  information needed for reader success, precise technical contracts, and verifying
  installation/recovery from the reader's actual starting point. Executed commands do
  not substitute for a fresh reader's understanding or independent factual review.

The initial project is derived from the trusted full reference by a reviewed targeted
mutation. The implementation, task and oracle hashes identify this public version.
Each oracle requires a positive control to prevent universal rejection/error-only behavior
from passing. Wrong controls establish sensitivity to specific failures, not exhaustive
adequacy. Extend controls when a pilot finds a blind spot; version/fingerprint the case and
never silently pool it with the earlier version.

Independent review should record artifact fingerprint, exact case/phase, reviewer identity,
source examined, objective evidence and the explicit review question from the manifest.
Maintain `needs_review` until that review occurs. If a structural dimension is not observable
without the fresh-maintainer sequel, leave it unassessed. If prose states an unsupported
guarantee outside the executed examples, it fails fact review even when those examples pass.

For each pilot, inspect the actual initial catalog, actual named-role spawn events, source
access events, model/effort settings and budget accounting. Treat missing trace coverage as
unknown. Difficulty is a hypothesis, not calibrated simply because the curator knows the fix.
