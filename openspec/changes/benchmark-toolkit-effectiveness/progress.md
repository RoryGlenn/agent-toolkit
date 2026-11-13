# Implementation evidence

Tracked in [issue #25](https://github.com/RoryGlenn/agent-toolkit/issues/25).

## Implemented

- The one-file demo stages the same Git diff and prompt for stock Codex and
  the actual default project bootstrap. The offline controls verify startup
  and rollback on the original, seeded, and clean files.
- Version 2 of the existing benchmark plans stock, single-agent, default
  toolkit, generic worker, and named worker conditions. Every current role
  has two public cases. The 40-session calibration schedule is reproducible.
- The report seals evidence, supports blind packets and independent grading,
  and retains failed, interrupted, and unverified attempts. Private held-out
  task manifests and analysis rules can be frozen without sending them to actors.
  The public report is a structured projection. It excludes raw output and
  free-form grading evidence, which can be reviewed and excerpted separately.

## Independent review

Review and verification identified native catalog, no-fork worker, permission
denial, and grading gaps. The updated runner checks the actual project catalog,
recognizes native read-only errors, and requires a verifiable coordinator handoff,
worker turn, and matched brief. The generic worker has neutral instructions to
avoid inheriting the coordinator role. Provider and tool-surface failures stay
separate from task scores. Legacy regression tests and review judgments require
their own evidence.

Controlled per-role runs target the direct-tool native V1 profile. The bundled
model catalog and actual prompt tool surface are checked before execution. A
version with a different worker protocol or missing native traces remains
unqualified for controlled role results.

## Live results

The four scheduled SQLite demo slots reached native preflight on the managed
Linux host. All four ended in setup errors because Bubblewrap could not create
its loopback NETLINK_ROUTE socket. The host stopped before authentication was
staged or any model was invoked. Both pairs remain incomplete, with no
measured quality, dispatch, latency, or usage results.

The live study is tracked in [issue #27](https://github.com/RoryGlenn/agent-toolkit/issues/27).
Run the demo and calibration on a signed-in Codex CLI host that passes the native
checks. Curate private held-out cases and freeze the study after calibration.
Quantitative claims need that run and independent grades.
