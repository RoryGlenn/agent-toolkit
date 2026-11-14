# Public benchmark evidence

## Purpose

Give prospective users enough evidence to reproduce the demo and see which
toolkit capabilities improved outcomes under the published conditions.

## ADDED Requirements

### Requirement: Publish attributable comparison results

The public report SHALL identify the toolkit revision, host and model, tested
profile, task set, grading criteria, distinct task count, repetitions, coverage,
attempt outcomes, and paired uncertainty. It SHALL link reproducible commands and
sanitized evidence for all planned conditions.

#### Scenario: A role has mixed outcomes

- **WHEN** a comparison includes wins, ties, losses, and incomplete pairs
- **THEN** the report exposes each count and the corresponding denominator
- **AND** readers can trace an outcome to its frozen task, output, and grade

#### Scenario: One case is repeated

- **WHEN** several fresh sessions run the same task
- **THEN** the report counts one distinct task and identifies the repeated attempts

### Requirement: Show quality, elapsed time, and usage together

Reports SHALL show task outcomes, time, and model usage by tested condition.
Usage SHALL distinguish root-only telemetry from run-wide totals, and cost SHALL
use an identified price basis when it can be estimated.

#### Scenario: Child usage is unavailable

- **WHEN** the host emits root tokens but omits some child usage
- **THEN** the report displays observed root usage and marks run-wide usage and
  dependent costs as unavailable

### Requirement: Match public claims to evidence

The README and report SHALL distinguish demo, exploratory pilot, and confirmatory
results. A claim of improvement SHALL meet criteria frozen before the confirmatory
run and identify the tested host, model, profile, and task population.

#### Scenario: A demonstration wins one pair

- **WHEN** the demo shows a better toolkit review on the seeded diff
- **THEN** the README can show that observed example and links the run evidence
- **AND** the README describes the result as one example on that diff

#### Scenario: Results are mixed or uncertainty includes no lift

- **WHEN** the confirmatory comparison misses the predefined success rule
- **THEN** the report shows the observed results and the supported claim scope

### Requirement: Keep private inputs out of published evidence

Public artifacts SHALL contain original redistributable fixtures and sanitized
evidence. Private sources, credentials, private paths, and raw session material
SHALL be excluded. Sanitized projections SHALL retain enough provenance to verify
how reported outcomes were derived.

#### Scenario: A session uses material that cannot be published

- **WHEN** the report is prepared for public release
- **THEN** the public projection shows the source profile and its limitations
- **AND** source text, sensitive metadata, and raw traces remain outside that release
