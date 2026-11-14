# Spec Delta

## Purpose

Use upstream change planning in opted-in projects while retaining engineering judgment, proportionate work, and independently supported completion evidence.

## ADDED Requirements

### Requirement: Single upstream change record
For substantial work in an opted-in OpenSpec project, the implementation skill SHALL use upstream workflows directly for planning, task tracking, specification synchronization and archive. It MUST keep progress in one change task record and link reviews and delivery evidence to the accepted requirement instead of duplicating checklists.

#### Scenario: Substantial change lifecycle
- **WHEN** a substantial accepted change uses OpenSpec
- **THEN** its requirements reach one writer, independent review and verification, tests, synchronized main specifications and archive with one maintained implementation checklist

### Requirement: Retained authority and proportionate fallback
Original accepted scope, project decisions and user authorization MUST remain authoritative. Specifications MUST NOT authorize external effects or silently resolve conflicts. Ordinary projects and trivial work SHALL retain a proportionate path without OpenSpec. Missing tooling MUST be disclosed while useful checks continue without fabricated execution claims.

#### Scenario: Conflicting requirement
- **WHEN** a specification expands or contradicts the accepted requirement
- **THEN** the conflict is surfaced and accepted scope is resolved before dependent implementation

#### Scenario: Ordinary project or trivial edit
- **WHEN** the project has not opted in or the request is trivial
- **THEN** the existing useful checks remain available without installing OpenSpec or requiring change artifacts

#### Scenario: Missing CLI
- **WHEN** the selected upstream workflow needs an unavailable CLI
- **THEN** the limitation and unrun operations are reported honestly while existing checks continue within scope

### Requirement: Bounded maintenance decision
Adoption evidence SHALL distinguish first-party guidance simplified, implementation code added, project records, unchanged generated files, remaining upgrade obligations, handoff results, rework and unavailable measurements. It MUST NOT infer general quality, speed or cost improvements from structural checks or one exercise.

#### Scenario: Continued opt-in recommendation
- **WHEN** one substantial exercise completes
- **THEN** the recommendation is based on its observed maintenance effects, retains evidence limits and leaves broader defaults to a separate decision
