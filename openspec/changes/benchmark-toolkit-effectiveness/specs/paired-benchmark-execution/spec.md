# Paired benchmark execution

## Purpose

Run reproducible comparisons between Agent Toolkit and stock Codex with the same
starting task, known settings, and evidence for every scheduled attempt.

## ADDED Requirements

### Requirement: Reproduce the minimal review demo

The demo SHALL prepare two fresh copies of the same one-file SQLite project and
apply the same review diff to each. It SHALL provide the exact review prompt and a
separate command that verifies the behavior after the reviews.

#### Scenario: Refactor passes startup and breaks rollback

- **WHEN** the operator starts the ledger, inserts a row in a caller-owned transaction,
  reruns setup, and rolls back under legacy SQLite transaction control
- **THEN** startup succeeds for both variants, the original leaves zero rows, and
  the seeded refactor leaves one row
- **AND** both review sessions receive “Review this diff.” with identical product
  code and diff bytes

#### Scenario: Clean change preserves rollback

- **WHEN** the operator runs the same check on the clean control
- **THEN** the caller's insert rolls back and the grader can detect unsupported
  material findings

### Requirement: Freeze each comparison before execution

A plan SHALL record the exact task, prompt, fixtures, grading contract, arm settings,
host, model, effort, tools, source access, budgets, repetitions, and planned order.
Attempts SHALL use fresh workspaces and sessions. Purposeful treatment differences
SHALL be declared in the plan.

#### Scenario: A matched pair is prepared

- **WHEN** the operator stages a pair
- **THEN** the prompt and starting product inputs have matching hashes, and the
  installed guidance and role assignment match the declared treatment

#### Scenario: An input changes after scheduling

- **WHEN** a frozen benchmark input or runner identity differs from the plan
- **THEN** execution refuses that attempt and retains the plan and mismatch for inspection

### Requirement: Qualify isolation on the actual host

The runner SHALL check project access, native permission enforcement, role discovery
as applicable, and separation from grader and other-arm files on the target host.
Actor actions SHALL stay within the rights declared for that task.

#### Scenario: Native setup fails before the model runs

- **WHEN** the host cannot establish the planned sandbox or prompt surface
- **THEN** the attempt is recorded as a setup failure with the failed check
- **AND** it produces no comparative quality score

#### Scenario: Actor starts a read-only review

- **WHEN** the fixture has a Git diff and the review is ready to start
- **THEN** the actor can read the diff and run permitted checks, and product files,
  expected answers, peer artifacts, and controller records retain their declared boundaries

### Requirement: Keep every scheduled attempt accountable

The runner SHALL retain every slot and its disposition, including unstarted,
incomplete, timed-out, or failed runs. The report SHALL distinguish host or harness
failures from task failures and bind grades to the exact submitted output.

#### Scenario: The campaign is interrupted

- **WHEN** the report is built with planned attempts that have no completed result
- **THEN** those slots remain visible and affected pairs are identified as incomplete

#### Scenario: A completed result changes after grading

- **WHEN** a frozen artifact, evidence file, or linked grade fails identity checks
- **THEN** the attempted comparison remains visible as invalid evidence and cannot
  supply a quality or cost claim
