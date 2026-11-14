# Spec Delta

## Purpose

Make task-appropriate toolkit expertise the default in the personal Codex profile
while preserving existing workflows, user constraints, and recoverable installation.

## ADDED Requirements

### Requirement: Stable reversible personal installation
The rollout SHALL install the complete selected toolkit catalog from one retained source checkout, preserve unrelated local work, and retain installation receipts and a verified pre-change snapshot. Installation status SHALL remain distinct from evidence of host loading or model behavior.

#### Scenario: Refresh an older checkout with overlapping local files
- **WHEN** a fast-forward update would replace existing untracked project files
- **THEN** their original contents and hashes are retained privately and differing local content remains available after the update
- **AND** existing installed sources remain usable throughout the migration

#### Scenario: Restore the personal installation
- **WHEN** the operator follows the recorded restore procedure
- **THEN** the previous selected installation and guidance can be restored without deleting independent source libraries or unrelated files

### Requirement: Explicit preservation of a legacy skill
The personal installer SHALL accept an explicit recognized legacy-skill preservation selection. It SHALL leave those existing aliases untouched, keep default alias migration unchanged, preserve normal canonical-destination conflict checks, and record the preservation selection in any resulting receipt.

#### Scenario: Preserve the established Doc Agent
- **WHEN** a full personal install explicitly preserves `doc-agent`
- **THEN** the original standalone package remains at its required path with unchanged content
- **AND** canonical `documentation-skill` and `documentation_agent` are installed normally

#### Scenario: Reject an unknown preservation selection
- **WHEN** an unrecognized legacy skill is requested for preservation
- **THEN** installation fails before creating directories or changing existing entries

### Requirement: Task-appropriate global routing
Global Codex guidance SHALL reuse the installed routing policy, explicitly request named-agent delegation for substantial specialist work, and request independent review and verification for nontrivial implementation. It SHALL retain user scope, single-writer ownership, explicit no-delegation constraints, and direct handling of trivial tasks.

#### Scenario: Ordinary substantive specialist request
- **WHEN** a fresh session receives a substantial in-scope specialist task without an agent name in its prompt
- **THEN** the session selects appropriate installed expertise and invokes the matching named agent
- **AND** the primary session incorporates the returned result

#### Scenario: Trivial or explicitly nondelegated work
- **WHEN** a request is trivial or the user explicitly prohibits delegation
- **THEN** no unnecessary child agent is required
- **AND** applicable skill guidance can be used directly

### Requirement: Preserve model intent and disclose incompatibility
The rollout SHALL inventory explicit role model settings, test required execution paths, and record any compatibility correction. Unavailable models SHALL not be silently replaced with another provider or an arbitrary model. Corrected roles can inherit the user's established parent configuration after preserving the original source and recording the change.

#### Scenario: Obsolete pinned model fails
- **WHEN** an actual required role path fails because its pinned model is unavailable
- **THEN** the failed attempt is retained separately
- **AND** a documented correction to parent-model inheritance is tested before that role is reported usable

### Requirement: Surface-specific verification
Verification SHALL distinguish actual CLI, IDE, and desktop execution from backend discovery or shared-file inspection. Each surface SHALL receive a completed result or a precise evidenced limitation, with available independent checks continuing when a surface cannot be controlled.

#### Scenario: Real natural-routing check
- **WHEN** a synthetic task is run through a fresh controllable surface outside the toolkit
- **THEN** its receipt identifies the surface, source revision, configuration, actual skill or role events, and independently checked outcome

#### Scenario: Surface automation is unavailable
- **WHEN** no authorized control path can complete a real IDE or desktop task
- **THEN** the record identifies the attempted routes and exact limitation
- **AND** it does not label CLI or app-server backend evidence as a completed UI verification
