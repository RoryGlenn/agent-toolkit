# Benchmark Agent Toolkit effectiveness

## Why

Developers deciding whether to install Agent Toolkit need to see how it changes the
outcome of ordinary work on their AI client. A small reproducible demo and paired
results for the toolkit and each named role can show where the extra workflow earns
its time and token cost.

## What Changes

- Add a public one-file SQLite review demo with the prompt **“Review this diff.”**
  Compare stock Codex and the default Codex project bootstrap on the same diff.
  Include a clean control and an executable check for the seeded rollback regression.
- Extend the existing Python benchmark to compare stock Codex with the default
  Agent Toolkit installation. Preserve a stock single-agent control for users who
  want to measure against a session with child agents disabled.
- Evaluate all seven current Codex named roles on their intended work against stock
  Codex with child agents disabled. In a second comparison, assign the same task to
  a generic worker and the named worker through the same workflow. Measure normal
  toolkit routing in the full-toolkit comparison.
- Publish a README entry, a reproducible demo, and a versioned report with raw
  sanitized evidence, uncertainty, resource use, and outcomes for each role.
  Include ties, regressions, timeouts, and limitations alongside favorable results.

## Capabilities

### New Capabilities

- **paired-benchmark-execution** provides reproducible demo fixtures, frozen paired
  campaigns, a stock baseline, and qualified execution evidence.
- **agent-role-evaluation** compares the default toolkit and each named Codex role on
  representative tasks with graded outcomes and observed role execution.
- **public-benchmark-evidence** produces verifiable comparisons for the README and
  per-role results, with claim scope and cost visible.

### Modified Capabilities

None. The repository has no synchronized capability specifications for the benchmark.

## Impact

Implementation will extend `benchmarks/`, its tests, and its documentation. It will
reuse the existing planner, process isolation, artifact sealing, and report paths.
The initial campaign targets Codex CLI on a qualified Ubuntu or macOS host. Copilot
and other hosts require their own matched results.

The public demo and live results are future deliverables under this change. The
initial SQLite fixture has been exercised locally. The earlier A/B trial stopped at
Codex sandbox setup before either review ran.
