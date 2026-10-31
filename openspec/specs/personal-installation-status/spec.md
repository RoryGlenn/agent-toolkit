# personal-installation-status Specification

## Purpose
Allow users to inspect the intended linkage of selected personal installation destinations without changing their source or host files.

## Requirements

### Requirement: Inspect the installation selection
The CLI SHALL accept `status --target codex|copilot (--skill NAME ... | --all) --home PATH [--codex-home PATH] [--json]`, applying install aliases, dependency closure and role associations. Explicit home SHALL ignore inherited CODEX_HOME. Copilot SHALL report skills only. Each expected destination SHALL occur once.

#### Scenario: Shared dependencies and aliases
- **WHEN** repeated aliases and overlapping skills are selected
- **THEN** status reports canonical skills, dependencies and associated roles once each.

#### Scenario: Explicit destination roots
- **WHEN** status is run with an explicit home and optional Codex home
- **THEN** only those selected host destinations are inspected, ignoring inherited CODEX_HOME.

### Requirement: Classify intended linkage
Each expected destination SHALL report current, missing or different. A current skill SHALL be a symlink with the installer's canonical absolute current-source target. A current Codex role SHALL be a regular hardlink sharing the current source inode. Any other present entry SHALL be different regardless of equal bytes.

#### Scenario: Present but detached entries
- **WHEN** a skill is copied or foreign-linked, or a role is copied, symlinked or detached by atomic source replacement
- **THEN** its state is different, even if contents match.

#### Scenario: Absent destinations
- **WHEN** an expected destination does not exist
- **THEN** its state is missing, while a dangling symlink is different.

### Requirement: Stable output and exit status
Human output SHALL be the default. JSON mode SHALL emit exactly one object with schema_version 1 and entries sorted by area and name, each containing area, name and state. Status SHALL return zero only when every expected entry is current and nonzero for missing, different or invalid input.

#### Scenario: Mixed result
- **WHEN** JSON status observes missing and current entries
- **THEN** one versioned object lists their sorted states and the exit status is nonzero.

#### Scenario: A selected home contains a symlink loop
- **WHEN** JSON status cannot resolve an explicit home or Codex home because it contains a symlink loop
- **THEN** status returns nonzero, emits one versioned object with empty entries and an error string, reports the error on stderr without a traceback, and leaves the source and host trees unchanged.

### Requirement: Read-only inspection with limited claims
Status SHALL NOT create directories or receipts, replace links, repair entries, or infer overwrite permission or historical ownership. Documentation SHALL explain that linkage does not establish host loading or distinguish outdated-owned from user-edited content.

#### Scenario: Missing home and conflicting entries
- **WHEN** status examines an absent home or existing foreign entries
- **THEN** the source and host trees remain unchanged and no repair is attempted.
