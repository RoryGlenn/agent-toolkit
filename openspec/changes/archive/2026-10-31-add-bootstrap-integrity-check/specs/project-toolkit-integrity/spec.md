# Spec Delta

## Purpose

Allow collaborators to verify recorded project toolkit integrity without modifying their installation or requiring the current source package to match it.

## ADDED Requirements

### Requirement: Recorded integrity check
The CLI SHALL support `bootstrap --project PATH --check`, returning zero with a human-readable intact result only when the recorded manifest, owned file contents, and managed AGENTS.md routing block are valid and intact.

#### Scenario: Intact installation
- **WHEN** the command checks an intact bootstrapped project
- **THEN** it exits zero and reports integrity success

#### Scenario: Managed content drift
- **WHEN** an owned file is missing or edited or the managed routing block is missing, edited, incomplete, or duplicated
- **THEN** the command exits nonzero and identifies the failing file or routing block

#### Scenario: Invalid installation record
- **WHEN** the target is unbootstrapped or its manifest is malformed or contains unsafe owned paths or hashes
- **THEN** the command exits nonzero with an explanatory result before trusting unsafe paths

### Requirement: Read-only operation
The command MUST preserve files and instructions, MUST NOT create a missing target, and MUST NOT write bytecode, manifests, or generated files in the target.

#### Scenario: Success and failure preserve target
- **WHEN** integrity checking succeeds or fails
- **THEN** target entries, identities, permissions, and bytes remain unchanged

#### Scenario: Missing target
- **WHEN** the target does not exist
- **THEN** the command fails without creating it

### Requirement: Recorded ownership boundary
The command SHALL compare to recorded hashes independently of current source changes. Extra unowned files and edits outside the managed AGENTS.md block MUST NOT count as drift.

#### Scenario: Local additions and newer source
- **WHEN** source packages change or disappear and the project gains unrelated files or instructions outside the block
- **THEN** an otherwise intact installation passes

### Requirement: Exclusive check mode
The command MUST reject check combined with `--update`, `--dry-run`, `--skill`, `--all`, or `--target` without modifying the project. Normal bootstrap and update behavior SHALL remain supported.

#### Scenario: Incompatible options
- **WHEN** check is combined with any forbidden option
- **THEN** the CLI exits nonzero and explains the incompatible option
