# toolkit-usage-audit Specification

## Purpose
Let the workstation owner inspect real toolkit usage locally without exporting
conversation content or confusing discovery, execution, eligibility, and quality.

## Requirements

### Requirement: Bounded local read-only inspection
The audit SHALL read only explicitly selected local session traces or a bounded recent-session selection. It SHALL make no network calls, execute no trace content, create no schedule, and change no source traces. Its JSON report SHALL omit prompts, responses, reasoning, command bodies, credentials, and book content.

#### Scenario: Audit selected local sessions
- **WHEN** the operator supplies a local session root and a session-count or time bound
- **THEN** the audit reports its selection and counts using only local reads
- **AND** the source traces retain their original bytes

#### Scenario: Malformed or unsupported trace
- **WHEN** an input line is malformed, truncated, encrypted, or uses an unsupported envelope
- **THEN** the audit reports an explicit limitation or unknown evidence
- **AND** it does not execute embedded text or fabricate successful use

### Requirement: Separate observed usage categories
The audit SHALL distinguish tool-observed skill reads, attempted role calls, actual named-child starts, completed children, failed or unresolved calls, and independently checked task outcomes. A catalog entry, instruction mention, spawn acknowledgement, or final self-report alone SHALL not establish a completed named-agent run.

#### Scenario: Named role starts and completes
- **WHEN** parent-linked child metadata identifies a toolkit role and its own terminal event records completion
- **THEN** the audit reports an observed start and completion for that role
- **AND** it does not infer task correctness from those events

#### Scenario: Inherited parent history appears in a child
- **WHEN** a child trace repeats a parent call before the child's own task begins
- **THEN** that inherited call is not counted as an additional child action or recursive delegation

#### Scenario: Role acknowledgement is missing
- **WHEN** a spawn tool call has no successful acknowledgement but a linked child trace exists
- **THEN** actual child-start evidence is retained separately from the unresolved acknowledgement

### Requirement: Explicit eligibility and skips
The audit SHALL require operator-supplied case expectations before labeling an absent role a routing miss. It SHALL report unspecified eligibility as unknown, distinguish allowed direct skill use from required delegation, and keep justified skips and unsupported surfaces separate from passes.

#### Scenario: Ordinary trace without an eligibility declaration
- **WHEN** a trace contains no named child and no declared expected role
- **THEN** it reports observed use only with eligibility unknown
- **AND** it does not report a routing failure or an adoption percentage

#### Scenario: Required agent is absent
- **WHEN** a declared verification case requires a role and no linked execution of that role is observed
- **THEN** the case is reported as a routing miss or incomplete evidence
- **AND** any independently checked result remains a separate field

### Requirement: Reproducible evidence and conservative results
Reports SHALL identify their schema, inspected trace hashes, available source identity, selection bounds, and parsing limits. Partial coverage SHALL be labeled partial. Full adoption, comparative quality, and untested UI behavior SHALL not be inferred from bounded smoke tests.

#### Scenario: Check a bounded rollout manifest
- **WHEN** the operator audits the synthetic rollout cases and their checked outcomes
- **THEN** the report can be reproduced from the identified local traces and manifest
- **AND** unsupported surfaces and unverified outcomes remain visible
