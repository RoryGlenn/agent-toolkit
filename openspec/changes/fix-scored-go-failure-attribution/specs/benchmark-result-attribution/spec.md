# Spec Delta

## Purpose

Keep completed submission failures separate from unavailable test execution so benchmark reports preserve objective failure evidence.

## ADDED Requirements

### Requirement: Attribute completed scored Go failures
The benchmark SHALL report completed assertion failures and detected data races in scored Go submissions as candidate failures, preserving failure evidence and a false objective outcome.

#### Scenario: Additional queue test fails
- **WHEN** a scored submission completes the full queue test run with a terminal assertion failure and an ordinary failure exit
- **THEN** its grade is failed with the failing command recorded rather than a harness error

#### Scenario: Scored submission introduces a data race
- **WHEN** the race detector reports a race during a scored Go run with complete terminal test outcomes and an ordinary failure exit
- **THEN** its grade is failed and its objective outcome is false

### Requirement: Preserve trusted qualification controls
Trusted parent and reference qualification SHALL remain strict: an unexpected data race or failing full-queue diagnostic cannot establish the intended behavioral qualification.

#### Scenario: Broken parent races instead of reproducing the regression
- **WHEN** a trusted negative control reports a data race even though a behavioral failure was expected
- **THEN** qualification remains unavailable rather than accepting that output as the expected regression

### Requirement: Preserve unavailable-execution evidence
Missing terminal outcomes, skipped required tests, timeouts, truncated output, signals, and resource faults SHALL remain unavailable execution rather than candidate test failures.

#### Scenario: Race output is incomplete
- **WHEN** a scored run reports a race but required terminal outcomes are missing
- **THEN** its result remains an environment failure with objective outcome unknown
