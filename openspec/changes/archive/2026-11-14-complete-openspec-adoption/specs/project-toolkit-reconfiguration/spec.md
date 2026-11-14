# Spec Delta

## Purpose

Let projects deliberately change toolkit capabilities and hosts while preserving recorded ownership, local changes, and recoverable upgrades.

## ADDED Requirements

### Requirement: Explicit reconfiguration
The CLI SHALL support `bootstrap --reconfigure` for existing projects. It MUST require a skill or host selection, reject combination with `--update`, and use the complete explicit skill selection as requested roots. Normal repeat and update MUST reject unrelated selection changes.

#### Scenario: Deliberate capability and host change
- **WHEN** an existing project previews and applies a complete requested selection with `--reconfigure --skill NAME --target HOST`
- **THEN** it reports the complete file plan before mutation and installs only the requested closure and selected host roles

#### Scenario: Invalid mode or missing installation
- **WHEN** reconfiguration is combined with update, has no selection, or targets an unbootstrapped project
- **THEN** it fails without changing the target

### Requirement: Honest selection migration
New installations SHALL record v2 requested roots separately from resolved skills. V1 repeat/update SHALL preserve all recorded skills without inferring roots or silently migrating. V1 reconfiguration MUST require a complete explicit skill selection; v2 host-only reconfiguration SHALL reuse known roots.

#### Scenario: Legacy explicit migration
- **WHEN** a v1 project is reconfigured with an explicit complete skill selection
- **THEN** the new v2 record contains that selection and its dependency closure after validating old ownership

#### Scenario: Ambiguous legacy host-only migration
- **WHEN** a v1 project requests only a new host
- **THEN** it fails with instructions to declare the complete requested skills and preserves the old record

### Requirement: Historical ownership independent of catalog
Recorded v1/v2 paths, hashes, hosts, skill names and provenance SHALL be validated independently of the live catalog. An obsolete skill MUST remain inspectable and explicitly retireable. Ordinary update MUST refuse an unavailable retained selection without removing it.

#### Scenario: Removed source package
- **WHEN** a recorded skill disappears from the current catalog and the user explicitly selects surviving capabilities
- **THEN** reconfiguration can retire unchanged owned files using their recorded identities without requiring the removed source

### Requirement: Protected retirement and recovery
Reconfiguration MUST preflight every old and desired file and the routing block before mutation, reject missing/edited owned files, unmanaged collisions and unsafe paths, preserve unowned content and required shared dependencies, and roll back ordinary failures with the manifest committed last.

#### Scenario: Shared dependency and upstream coexistence
- **WHEN** one capability is retired while another still uses its dependency and the project contains OpenSpec-generated files
- **THEN** required shared resources and unowned upstream content remain intact while only unchanged obsolete owned files are removed

#### Scenario: Refusal or late failure
- **WHEN** preflight detects an edited file, missing file, collision, link, unsafe record, or a later write fails
- **THEN** preflight failures perform no writes and ordinary write failures restore prior bytes and modes or explicitly report concurrent-edit recovery limits
