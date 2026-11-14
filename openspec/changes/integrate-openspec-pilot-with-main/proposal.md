# Proposal

## Why

PR #19 no longer merges cleanly with current main. Reconcile its documentation and
OpenSpec configuration while retaining the pilot's CLI behavior and newer toolkit capabilities.

## What Changes

- Integrate main `68ea80d5decb7df8f4cccb59f1e7f2df53e579ec` into the isolated PR worktree.
- Retain the reorganized README and add the pilot's three CLI inspection commands and opt-in OpenSpec guidance.
- Preserve the pilot configuration, frozen experiment evidence, generated upstream files, and newer legacy-code capability.
- Re-run feature probes, repository checks, and independent review against the resulting source.

## Capabilities

No requirement changes. This is integration and documentation maintenance; `skip_specs: true` applies.

## Impact

README, OpenSpec project configuration, and integration evidence. No new runtime
dependency, default selection change, personal installation, or capability retirement.
Commit, push, and merge remain separate delivery actions under the user's repository rules.
