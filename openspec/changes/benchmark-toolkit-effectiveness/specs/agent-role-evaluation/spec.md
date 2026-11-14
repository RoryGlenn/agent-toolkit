# Agent role evaluation

## Purpose

Measure the default project installation as users encounter it and each named
Codex role's contribution in the work it was designed to perform.

## ADDED Requirements

### Requirement: Compare ordinary use with the actual default installation

The full-toolkit comparison SHALL use stock Codex with native capabilities available
and the default Agent Toolkit Codex project bootstrap. Both SHALL receive the same
ordinary user prompt. A stock session with child agents disabled SHALL be available
as a separately identified comparison.

#### Scenario: User requests implementation or review

- **WHEN** an ordinary task runs in both headline arms
- **THEN** no named role or skill is requested by the prompt, the normal host can
  choose its available tools, and the report records observed toolkit use

#### Scenario: User requests a trivial change

- **WHEN** the suite includes a routine low-risk change
- **THEN** the report records task correctness, out-of-scope changes, delegation,
  and overhead for both arms

### Requirement: Cover every shipped named role

The evaluator SHALL derive its named-role coverage from the canonical Codex role
inventory. Each role SHALL have task-specific cases, a predeclared grading contract,
and comparisons with stock single-agent Codex and a matched generic worker. Roles
outside the default installation SHALL have a separate selective-install path.

#### Scenario: A named specialist handles a task also given to stock Codex

- **WHEN** the named worker and stock single-agent Codex receive the same bounded
  task and starting evidence
- **THEN** their outputs are graded with the same contract and the report includes
  the full elapsed time and observable resource use for each path

#### Scenario: The default project omits the legacy code role

- **WHEN** the legacy-code comparison is scheduled
- **THEN** it selects the legacy-code package and its required dependencies and
  reports that role under its selective-install treatment

#### Scenario: A named role has no matched case

- **WHEN** a coverage report is built
- **THEN** the role appears with its evidence gap and no inferred quality result

### Requirement: Measure the assigned role within a fixed workflow

The per-role controlled comparison SHALL keep task text, assigned scope, model,
effort, tools, permissions, source material, and other workflow participants
matched. The deliberate treatment is the named role's instructions and its
associated skill guidance. Dispatch SHALL be established from execution evidence.

#### Scenario: A reviewer and a generic worker inspect the same diff

- **WHEN** both receive the frozen requirement and diff
- **THEN** their reviewed bytes and authority match, and the evaluator can distinguish
  the named dispatch from a generic dispatch

#### Scenario: Only discovery is observed

- **WHEN** the named role appears in configuration or in the final answer but its
  execution cannot be verified
- **THEN** the report identifies dispatch as unverified and supplies no
  role-execution credit

### Requirement: Grade user-visible outcomes and unnecessary work

Cases SHALL use executable checks where the contract permits them. Criteria requiring
judgment SHALL be fixed before execution and graded independently on frozen outputs.
The suite SHALL include clean or adjacent cases to measure false findings, scope
drift, and extra process.

#### Scenario: Reviewer spots a real regression on a seeded diff

- **WHEN** a review identifies a material issue
- **THEN** the grader checks the changed path, trigger, observable consequence, and
  supporting evidence against the predeclared rubric

#### Scenario: Agent claims a check passed without evidence

- **WHEN** no corresponding evidence exists or the executable check fails
- **THEN** the claim earns no verification credit

#### Scenario: Trusted grading controls are incorrect

- **WHEN** the correct control fails, the wrong control passes, or the grader errors
- **THEN** the case is ineligible for model comparison until the controls are corrected
