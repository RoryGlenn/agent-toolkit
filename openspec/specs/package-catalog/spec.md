# package-catalog Specification

## Purpose
Expose the packaged skills and their associated runtime roles for people and automation without changing host installation state.

## Requirements

### Requirement: Versioned JSON catalog

`python3 install.py list --json` SHALL emit exactly one JSON object on stdout with `schema_version` equal to integer `1` and `skills` sorted by canonical name. Each entry SHALL contain `name`, `description`, sorted direct `dependencies`, and `roles` mapping every supported host to sorted actual runtime role names. Skill-only hosts SHALL have empty role lists.

#### Scenario: Machine-readable inventory

- **WHEN** a valid package is listed with `--json`
- **THEN** stdout parses as one object with the specified fields and deterministic list ordering
- **AND** metadata, direct dependencies, and roles reflect the current validated package and associations

#### Scenario: Direct dependencies only

- **GIVEN** a skill depends on another skill that has its own dependency
- **WHEN** the JSON catalog is requested
- **THEN** the first skill lists only its direct dependencies, while every packaged skill appears separately

### Requirement: Catalog validation and read-only operation

The JSON catalog SHALL validate package sources and dependency availability before producing output, return nonzero on invalid input with diagnostics on stderr, and SHALL NOT read user configuration or create or modify source files, user configuration, or installation directories.

#### Scenario: Invalid package

- **WHEN** a role definition or required skill is invalid or missing
- **THEN** JSON listing fails with empty stdout and a diagnostic on stderr

#### Scenario: No installation state

- **WHEN** JSON listing runs with no existing host directories or with existing host files
- **THEN** those directories remain absent or unchanged and the source package remains unchanged

### Requirement: Human catalog compatibility

`python3 install.py list` without `--json` SHALL retain its existing human-readable catalog output and command behavior.

#### Scenario: Default listing

- **WHEN** list is invoked without `--json`
- **THEN** the existing banner, descriptions, host role lines, and spacing are preserved
