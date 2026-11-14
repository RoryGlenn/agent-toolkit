# Proposal

## Why

Agent Toolkit is only partly installed in the personal Codex profile, and general
sessions have no explicit requirement to delegate appropriate work to its named
agents. Make real toolkit use the default across this workstation's local Codex
surfaces and distinguish installed files from observed skill use, completed agent
execution, and a useful result.

## What Changes

- Retain a private, hashed pre-change snapshot of global guidance, installation
  links and receipts, and overlapping local project files. Refresh the stable
  `/home/ubuntu/repos/agent-toolkit` checkout without losing existing work.
- Install all selected toolkit skills and seven named Codex agents from that
  stable checkout using reversible installation receipts. Preserve the user's
  mandated standalone Doc Agent path and review model overrides before rollout.
- Add a concise personal routing policy that reuses `task-routing-skill`, requests
  matching named agents for substantive specialist work, and retains lightweight
  handling for trivial requests and explicit no-delegation instructions.
- Verify fresh local CLI, IDE, and desktop paths with synthetic tasks outside the
  toolkit. Require actual role/skill execution evidence; disclose unavailable
  surface controls rather than substituting a backend run for a UI result.
- Add an on-demand, local-only audit of existing execution traces and a bounded
  verification manifest. Report skill reads, named-agent lifecycle evidence,
  independently declared eligibility, failures, justified skips, and unknowns
  separately, without exporting prompts, outputs, credentials, or book content.
- Keep a current implementation checklist, decisions, evidence, rollback steps,
  and remaining limits in this OpenSpec change. Save portable workstation
  guidance/restore instructions in private dotfiles without mixing unrelated edits.

## Capabilities

### New Capabilities

- `personal-toolkit-routing`: Reversible personal installation and explicit
  task-appropriate toolkit routing, with honest surface-specific validation.
- `toolkit-usage-audit`: Read-only, bounded, privacy-preserving local evidence of
  skill loading and named-agent use, with declared eligibility and uncertainty.

### Modified Capabilities

None. Existing installation status remains a linkage check; this change must not
relabel that status as proof of host loading or useful model behavior.

## Impact

Expected repository changes are a small audit command and focused tests, global
routing/setup documentation, this OpenSpec change, and only narrowly necessary
installer compatibility support if source inspection establishes it is needed.
Workstation changes cover the personal skill/role installation, global Codex
guidance, private audit evidence, and portable dotfiles restore material.

The user explicitly authorized planning followed by steps 1–4. No issue, commit,
push, PR, merge, publication, new cloud dependency, scheduled monitoring job,
unrelated process restart, or change to other applications' permissions is included.
Named toolkit agents remain Codex-only; other hosts may use portable skills.

This records the initial local-only authorization. The user later explicitly
authorized issue-to-merge delivery in
[issue #33](https://github.com/RoryGlenn/agent-toolkit/issues/33). The daily updater
has its own companion OpenSpec change; it is not part of the audit command.
