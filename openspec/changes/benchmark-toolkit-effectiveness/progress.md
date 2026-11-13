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

## Live results

The four scheduled SQLite demo slots reached native preflight on the managed
Linux host. All four ended in setup errors because Bubblewrap could not create
its loopback NETLINK_ROUTE socket. The host stopped before authentication was
staged or any model was invoked. Both pairs remain incomplete, with no
measured quality, dispatch, latency, or usage results.

The next evidence milestone is to run the demo and calibration on a signed-in
Codex CLI host that passes the native checks. Curate private held-out cases and
freeze the study after calibration. This change can publish the demo and
methodology now. Quantitative claims need the later run and independent grades.
