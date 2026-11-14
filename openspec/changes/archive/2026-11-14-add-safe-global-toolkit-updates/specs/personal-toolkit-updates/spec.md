# Spec Delta

## Purpose

Keep an existing personal Toolkit installation current with merged public changes
through a checked local operation that preserves unpublished work and recovery evidence.

## ADDED Requirements

### Requirement: Serialize and guard deployment
The updater SHALL serialize operations and require the configured clean branch, source identity, and current managed installation before deployment. It SHALL hold on tracked edits, untracked files, non-fast-forward history, incompatible layout, or foreign installed entries without discarding content.

#### Scenario: Unpublished local work
- **WHEN** a run finds tracked or untracked local work
- **THEN** it records a blocked-local-changes result and leaves source and global entries unchanged

#### Scenario: Concurrent or foreign work
- **WHEN** another updater holds the lock or an expected destination has been replaced
- **THEN** the run refuses deployment without overwriting that work

#### Scenario: Catalog retirement
- **WHEN** a candidate removes a managed entry or a refreshed runtime no longer enumerates a prior managed path that is still present
- **THEN** deployment is held for explicit reconciliation and the prior entry is preserved

### Requirement: Validate an exact upstream revision before deployment
The updater SHALL fetch only the configured public main branch and validate the exact candidate in a separate checkout before advancing the live source. It SHALL recheck source and destination identity before promotion and fail closed when a required check fails or is unavailable.

#### Scenario: Candidate check fails
- **WHEN** a candidate fails an automated deployment check
- **THEN** live source and installation stay at the prior revision and the failed check is recorded

#### Scenario: Source changes during validation
- **WHEN** source or managed destinations change after preflight
- **THEN** deployment is held and the concurrent change is preserved

### Requirement: Refresh and verify the personal installation
An accepted update SHALL fast-forward the retained checkout, refresh canonical skill links and regular agent hardlinks with receipt-backed backups, preserve the standalone Doc Agent, and require every expected entry to be current. Linkage and structural role validation SHALL remain distinct from actual model execution.

#### Scenario: Git replaces an agent source inode
- **WHEN** a validated update replaces an agent definition
- **THEN** the installed regular file shares the updated canonical inode and all selected entries report current

#### Scenario: Independent documentation workflow
- **WHEN** installation refresh runs
- **THEN** the preserved Doc Agent content remains unchanged

### Requirement: Recover interrupted or failed deployment
The updater SHALL persist prior and candidate revisions before mutation, retain receipts, and attempt guarded rollback after deployment failure or interruption. Recovery SHALL refuse unexpected edits, restore prior source and current hardlinks when possible, and otherwise expose a recovery-required result without forcing changes.

#### Scenario: Post-install verification fails
- **WHEN** verification fails after source promotion
- **THEN** guarded recovery restores the prior revision and verifies its current installation

#### Scenario: Interrupted update with subsequent user edits
- **WHEN** an unfinished deployment is found and its source or destinations no longer match the transaction
- **THEN** recovery stops with recorded recovery instructions and preserves the edits

#### Scenario: Operator rolls back an accepted revision
- **WHEN** the operator restores the prior revision and a scheduled run sees the same rolled-back upstream revision
- **THEN** deployment remains held until an explicit reviewed retry or a different upstream revision

#### Scenario: Another installation occurs after interruption
- **WHEN** a separate installation creates a new receipt against the same source, including in the same profile
- **THEN** recovery holds without restoring that receipt or the updater's receipt
- **AND** updater recovery uses only its exact journaled operation identities, including rollback repair

### Requirement: Operate locally with inspectable scheduling
The updater SHALL provide manual run and status commands, private local records, and an opt-in daily user timer that invokes a fixed reviewed runtime. It SHALL avoid model calls, publication, dependency installation, and private-data upload. Documentation SHALL describe the exact checks, fresh-session requirement, timer availability, holds, and rollback procedure.

#### Scenario: Daily workstation check
- **WHEN** the installed timer runs
- **THEN** the same guarded operation used by the manual command records its result
- **AND** a dirty checkout remains held without changing the working agents
