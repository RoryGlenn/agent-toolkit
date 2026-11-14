# Proposal

## Why

Completed Go assertion failures and data races in scored submissions are currently
reported as harness errors. This loses candidate failure evidence and prevents objective comparison.

## What Changes

- Distinguish scored submissions from trusted qualification controls when interpreting Go output.
- Attribute complete assertion/race failures to scored candidates while retaining strict control qualification.
- Preserve environment classifications for incomplete, skipped, timed-out, resource-faulted, or malformed execution.
- Integrate current main, retaining its locked CI checks alongside the opt-in qualification job.
- Remove identical runtime mount pairs when system Python's base prefix is already mounted.
- Verify regressions and attempt the existing model-free Linux qualification without weakening host policy or pass criteria.

## Capabilities

### New Capabilities

- `benchmark-result-attribution`: Attribute completed candidate test failures independently of harness and trusted-control failures.

### Modified Capabilities

None.

## Impact

Large-project result parsing, evaluator context, regression tests, benchmark documentation,
CI conflict resolution, and source-bound validation evidence. No model calls or comparison study.
