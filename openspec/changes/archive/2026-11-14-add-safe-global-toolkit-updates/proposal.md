# Proposal

## Why

Global skills follow the retained checkout, but Git can replace the source inode of
installed agent hardlinks. GitHub updates therefore need a checked, reversible local
deployment operation rather than an unattended pull.

## What Changes

- Add a local updater with manual run/status commands, exclusive locking, public-main
  fetch, isolated candidate validation, fast-forward-only deployment, and receipts.
- Refuse deployment with local edits, unexpected installed files, incompatible
  candidate layout, validation failure, or changed source during validation.
- Refresh all canonical global links while preserving the independent Doc Agent;
  verify linkage and support rollback to the prior revision and role inodes.
- Ship daily user-systemd templates and install a stable local command on this
  workstation. Keep contribution maintenance and GitHub publication separate.
- Explain fresh-session discovery, machine availability, the current unpublished-work
  hold, inspection, recovery, and restore instructions.

## Capabilities

### New Capabilities

- `personal-toolkit-updates`: Checked, serialized, reversible updates from public main
  into an already configured personal Codex installation.

### Modified Capabilities

None. Existing personal installation and status semantics remain authoritative.

## Impact

New Python standard-library orchestration, tests, systemd templates, operating
documentation, and portable restore guidance. No package installation, cloud service,
model call in the scheduled job, source commit, push, PR, or automatic cleanup.
The dirty workstation checkout must remain held until its unpublished work is
reconciled through separately authorized Git delivery.
