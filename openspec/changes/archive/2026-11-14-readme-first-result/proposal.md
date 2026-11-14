# Proposal

## Why

Agent Toolkit's README rewrite in [PR #24](https://github.com/RoryGlenn/agent-toolkit/pull/24)
gives newcomers a way to try the toolkit before they need migration or maintenance details.
[Issue #31](https://github.com/RoryGlenn/agent-toolkit/issues/31) makes that approach the default
when the documentation skill writes or substantially revises onboarding material.

## What Changes

- Give new readers one recommended path from prerequisites to a verifiable result.
- Keep essential setup and warnings visible and make advanced details easy to find.
- Evaluate a plain README request with a runnable fixture and keep the API reference case as a control.

## Capabilities

### New Capabilities

- `documentation-onboarding` gives first-time readers a clear path to a useful result.

### Modified Capabilities

## Impact

The packaged documentation skill, its evaluation cases, and the authoring review record.
The Codex role already uses the skill. Syncing the separate standalone Doc Agent is a follow-up.
