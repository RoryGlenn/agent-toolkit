# Legacy code toolkit integration

## Purpose

Make the legacy-code specialist discoverable and selectively installable through the existing toolkit while preserving project ownership, host settings, privacy, and truthful validation records.

## ADDED Requirements

### Requirement: Expose canonical skill and role identities

The toolkit SHALL expose `legacy-code-skill` with the display name Legacy Code Skill and a Codex role named `legacy_code_agent` in `legacy-code-agent.toml`. The role SHALL load the discovered skill and resolve its resources relative to that skill. It SHALL inherit the caller's model, reasoning, tools, and effective permissions.

#### Scenario: User selects the new capability

- **WHEN** the user lists packages or installs the legacy-code capability for Codex
- **THEN** the catalog, metadata, installed files, and invocation examples agree on the canonical skill and role identities
- **AND** the role introduces no model, reasoning, provider, or permission override

### Requirement: Install only the selected capability and dependencies

Explicit legacy-code selection SHALL install the skill, its shared task-routing dependency, and its Codex role where supported. The Copilot target SHALL install portable skills only. Existing default project selection SHALL remain unchanged; full-catalog selection SHALL include the new package.

#### Scenario: Selected personal Codex installation

- **WHEN** only `legacy-code-skill` is requested in an isolated home
- **THEN** the resulting installation contains that skill, task routing, and one Codex legacy-code role without unrelated specialists

#### Scenario: Existing default project bootstrap

- **WHEN** a new project is bootstrapped with the existing default selection
- **THEN** its selected skills and roles remain unchanged by the addition of the optional legacy-code package

#### Scenario: Copilot or full catalog is selected

- **WHEN** the new skill is selected for Copilot or the full catalog is requested
- **THEN** Copilot receives no named role file and the full catalog includes the new skill in its supported host layout

### Requirement: Preserve existing installation ownership

The new selection SHALL retain existing dry-run, collision refusal, receipt, update, rollback, and restore guarantees. Project copies SHALL remain relocatable. Restore SHALL preserve unrelated work and shared dependencies still required by another installed selection.

#### Scenario: Selected install is restored beside existing skills

- **WHEN** a legacy-code installation is restored while another selection still depends on task routing
- **THEN** legacy-code-owned entries are restored according to their receipt and the remaining selection keeps its required resources

#### Scenario: Managed project file was customized

- **WHEN** a project update encounters an edited legacy-code-owned file or an unmanaged collision
- **THEN** it refuses the conflicting update without discarding the customization or leaving a partial update

### Requirement: Route by outcome and retain task ownership

Shared routing SHALL distinguish safe-change/testability work from general software design, data guarantees, documentation, implementation, and verification. It SHALL preserve one primary task owner, bounded consultation, explicit no-delegation requests, and assigned-subtask boundaries.

#### Scenario: Mixed legacy and transaction task

- **WHEN** a change involves both a hard-to-test implementation and transaction correctness
- **THEN** routing retains one owner and uses relevant legacy and data-system guidance within bounded scopes
- **AND** the legacy specialist does not treat tests as proof of the transaction guarantee

#### Scenario: Conversation changes topic

- **WHEN** a legacy-code-selected role receives a documentation-only or general design request
- **THEN** it uses the shared routing contract rather than forcing that request through the legacy-code procedure

#### Scenario: Named role is unavailable

- **WHEN** the skill is available but the host cannot dispatch the custom role
- **THEN** the caller can use the skill directly and accurately identifies that fallback without claiming named-role execution

### Requirement: Maintain revision-bound and separate evidence

Adoption records SHALL cover the new skill, role, and substantively changed reviewed entrypoints. A reviewed status SHALL link an actual assessment and current entrypoint fingerprint. Historical observations SHALL retain their original scope. Format checks, source retrieval, skill behavior, routing, named-role execution, and comparative value SHALL be reported separately.

#### Scenario: Only deterministic checks have passed

- **WHEN** packaging, retrieval, and fixture tests pass but no model run has occurred
- **THEN** the assessment reports those successes and leaves live behavior, routing, and comparative quality explicitly unverified

#### Scenario: Reviewed routing instructions change

- **WHEN** the shared routing entrypoint is modified for the new capability
- **THEN** its affected contract is reassessed before its current review fingerprint is updated
- **AND** previous run records are not relabeled as evidence for the new revision

### Requirement: Evaluate observable behavior with isolated controls

The evaluation package SHALL include realistic positive, boundary, and failure cases with objective checks where feasible. Grading answers SHALL remain outside actor context. Comparative runs SHALL use matched conditions, retain failures, and disclose source/tool differences. Deterministic CI SHALL require no original book, credentials, paid model calls, or live external systems.

#### Scenario: Proposed refactor loses an effect

- **WHEN** an intentionally wrong control preserves output text but drops a required write
- **THEN** the relevant outcome checker rejects it while accepting the correct control

#### Scenario: One successful model run is observed

- **WHEN** a single explicitly invoked case passes
- **THEN** the record identifies smoke evidence without claiming reliable routing, broad design quality, or improvement over baseline

### Requirement: Give users an executable starting and recovery path

Documentation SHALL describe invocation boundaries, selective installation, source-library setup, a verifiable first retrieval, missing-source behavior, and receipt-based restoration. It SHALL distinguish library setup from source study and model execution, and describe the configured model-provider boundary separately from offline book operations.

#### Scenario: New user follows the setup instructions

- **WHEN** a user has a supported local EPUB and the documented Python environment
- **THEN** the instructions lead through an isolated selected installation, source verification, source retrieval, and an accurately qualified invocation example

#### Scenario: User restores the toolkit installation

- **WHEN** the user follows the documented receipt-based restore procedure
- **THEN** toolkit-owned links or copies are restored within the existing ownership rules and the independently managed private book library is preserved
