# Spec Delta

## MODIFIED Requirements

### Requirement: Exclusive check mode
The command MUST reject check combined with `--update`, `--reconfigure`, `--dry-run`, `--skill`, `--all`, or `--target` without modifying the project. Normal bootstrap and update behavior SHALL remain supported.

#### Scenario: Incompatible options
- **WHEN** check is combined with any forbidden option
- **THEN** the CLI exits nonzero and explains the incompatible option

## ADDED Requirements

### Requirement: Versioned recorded integrity
Integrity checking SHALL accept valid v1 and v2 records independently of the current catalog. V2 MUST contain a nonempty canonical sorted requested selection contained in its recorded resolved skills; malformed selection records MUST fail without writes.

#### Scenario: Both manifest versions
- **WHEN** an intact project uses either supported record version
- **THEN** recorded integrity checking succeeds without requiring current skill source files

#### Scenario: Invalid requested roots
- **WHEN** v2 roots are absent, empty, duplicated, unsafe, or outside the recorded skills
- **THEN** integrity checking fails without trusting unsafe paths or changing the project
