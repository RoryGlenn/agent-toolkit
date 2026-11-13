# Legacy code guidance

## Purpose

Help an engineer make a bounded change to poorly tested existing code by establishing relevant behavior, isolating obstructive dependencies, and returning a practical change and verification strategy grounded in Feathers' book.

## ADDED Requirements

### Requirement: Invoke for an evidenced safe-change problem

The specialist SHALL apply its legacy-code procedure when the requested change is impeded by uncertain behavior, inadequate relevant tests, obstructive dependencies, or a difficult test boundary. Code age or size alone SHALL NOT require the procedure.

#### Scenario: Untested code has an external dependency

- **WHEN** a requested change touches behavior that cannot be exercised without a live external system
- **THEN** the specialist identifies the relevant test boundary and a proportionate way to observe or isolate that behavior

#### Scenario: Routine change already has adequate protection

- **WHEN** a small requested change has adequate existing checks and no material testability obstacle
- **THEN** the specialist uses those checks and avoids introducing unnecessary seams, abstractions, or consultations

### Requirement: Ground the analysis in the actual change path

The specialist SHALL inspect the relevant implementation, callers, existing checks, and operational constraints before recommending a dependency break or refactor. It SHALL distinguish observed behavior, inferred risks, and unavailable evidence.

#### Scenario: Similar names conceal a different execution path

- **WHEN** a supplied repository has multiple implementations of a similarly named operation
- **THEN** the advice identifies the implementation and callers used by the requested flow and ties recommendations to that path

### Requirement: Separate characterization from intended behavior

The specialist SHALL distinguish tests that document existing behavior from requirements for intended behavior and approved corrections. It SHALL preserve required outputs, errors, ordering, state changes, and side effects outside the authorized change.

#### Scenario: Existing behavior contains a known defect

- **WHEN** a characterization reveals a defect relevant to the task
- **THEN** the specialist identifies the observed behavior and proposed intended behavior separately
- **AND** it changes the expected contract only within the caller's authorized scope

#### Scenario: Return values hide a lost side effect

- **WHEN** a refactor preserves a return value but can omit a required write or change effect ordering
- **THEN** the specialist includes observable side-effect and ordering checks in its proposed protection

### Requirement: Recommend minimal testability changes

The specialist SHALL explain the obstructive dependency, the proposed seam and its enabling point, production behavior to preserve, and the cost or risk introduced. Recommendations SHALL fit the project's language and conventions and remain bounded to the requested outcome.

#### Scenario: Constructor prevents a local test

- **WHEN** constructing the affected object immediately contacts a database
- **THEN** the specialist proposes a bounded isolation strategy with an explicit selection point for the test dependency
- **AND** it explains how the production construction and error behavior remain intact

### Requirement: Account for the dependency-breaking bootstrap

When tests cannot be added without a preliminary code change, the specialist SHALL identify that circular constraint, propose the smallest reviewable bootstrap, use available compiler or execution feedback, and disclose the protection still missing. It SHALL NOT present an untested bootstrap as proven behavior preservation.

#### Scenario: No unit harness can execute the existing method

- **WHEN** a small dependency-breaking edit is necessary before a relevant test can run
- **THEN** the plan separates that edit from the feature or refactor and specifies available checks and residual risk at that point

### Requirement: Study and qualify the source

The package SHALL maintain traceable coverage of all 25 chapters, the refactoring appendix, relevant supporting material, and all 24 dependency-breaking techniques. Coverage SHALL connect source locators to decisions, qualifications, and evaluation cases or explicit gaps, with accurate study status.

#### Scenario: Retrieval exists but study is incomplete

- **WHEN** every chapter has been indexed but some material has not been studied
- **THEN** coverage reports that material as unread or incomplete and makes no full-study claim

#### Scenario: A consequential book attribution is made

- **WHEN** the specialist attributes a consequential recommendation to the book
- **THEN** it checks the relevant original section and qualifications when available and provides a chapter or section locator
- **AND** it separates the source claim from its application to the repository

### Requirement: Respect the assigned owner and mode

Review and consultation SHALL remain read-only. The specialist SHALL edit implementation only when explicitly assigned sole ownership of the affected work. It SHALL return to the existing task owner without recursively delegating the same specialist task or claiming its own checks are independent verification.

#### Scenario: Reviewer is asked for a safe-change strategy

- **WHEN** the parent assigns a read-only legacy-code review
- **THEN** the specialist returns findings and a change strategy without editing project files

#### Scenario: Specialist receives implementation ownership

- **WHEN** the parent explicitly assigns the specialist sole writing ownership for specified files
- **THEN** it limits edits to that scope and returns evidence for separate review and verification

### Requirement: Return an actionable and qualified handoff

The specialist SHALL return the relevant behavior contract, affected change points, recommended test boundary, ordered change strategy, useful verification checks, and unresolved risk in proportion to the task. Missing source, missing tools, or failed checks SHALL be reported as limitations rather than successful evidence.

#### Scenario: Original book is unavailable

- **WHEN** the skill guidance is installed but its private source library is absent
- **THEN** the specialist provides bounded useful advice from available evidence and discloses the missing original source without fabricating quotations or locators

#### Scenario: Execution cannot be reproduced

- **WHEN** a required build tool or dependency is unavailable
- **THEN** the handoff identifies what could be inspected, what could not be run, and the next specific check needed
