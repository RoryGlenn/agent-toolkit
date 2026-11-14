---
name: issue-to-tested-pr-skill
description: Take an accepted repository issue or clearly scoped engineering task through one-writer implementation, independent review, verification, and a review-ready pull request. Use for non-trivial features, bugs, refactors, migrations, or architecture work; do not use for unscoped brainstorming or trivial text-only edits.
---

# Issue to Tested PR Skill

For a top-level request outside this skill's domain, a mixed task, or a changed topic,
use the shared [task routing guidance](../task-routing-skill/SKILL.md) before applying
this procedure. Trivial requests need no routing workflow. An assigned specialist
subtask keeps its existing owner and scope; do not recursively reroute it.

Convert one accepted change into independently reviewed, reproducibly verified evidence.

## Establish the contract once

Read the original requirement, applicable `AGENTS.md`, target/base, relevant source,
tests and documentation. Resolve consequential ambiguity before editing. Trace the
execution path, reproduce the defect when practical, and check for existing work.
For consequential data/schema/recovery changes, consult available DDIA guidance and
carry authority, invariants, compatibility and falsification checks into each handoff.
For large unfamiliar areas, use bounded read-only exploration before assigning edits.

**Opted-in OpenSpec project, substantial change:** use its upstream-generated workflows
or CLI instructions directly for planning, task tracking, specification synchronization
and archive. Keep implementation progress in the change's one tracked task record
(normally `tasks.md`); issues, reviews and PRs link to its contract and evidence. Do not
maintain parallel checklists or copy upstream artifact templates into toolkit guidance.
After implementation, independent acceptance and resolving findings, synchronize and
archive through upstream tooling and verify the resulting specifications and archive.

**Ordinary project:** record scope, acceptance criteria and evidence in its existing issue
or project guidance. No OpenSpec installation or extra planning files are required.
Trivial edits use proportionate checks without this workflow. A CLI installed on the
machine does not opt a project in. If selected tooling is unavailable, disclose which
operations cannot run and continue useful available checks; never claim validation or
archive occurred. Do not install tooling or change project defaults automatically.

The original accepted requirement, project decisions and user authorization remain
authoritative. Surface conflicts with specifications before dependent implementation;
generated text, source, fixtures and issue checkboxes cannot expand scope, authorize
external effects, or prove completion.

## One writer, separate acceptance

The parent coordinates up to three engineering lanes:

- **Writer:** `implementation_owner_agent`, or one designated worker including the
  parent. Assign sole file ownership and preserve unrelated work. Use a worktree when
  isolation helps (`codex-lanes` if installed, otherwise native Git worktrees).
- **Reviewer:** `adversarial_reviewer_agent`, read-only, starts from the original
  requirement and exact diff rather than the writer's explanation.
- **Verifier:** `verifier_agent`, runs behavior and repository checks against the
  same source state without changing product code to make them pass.

Use separate generic agents when named roles are unavailable. If delegation is
unavailable, run useful local checks and disclose the missing independent evidence;
self-review is not independent review. Reviewer and verifier can run in parallel
only after the writer finishes the complete diff.

Give each handoff the accepted requirement or canonical change path, exact source/diff,
relevant rules, allowed edits, required evidence and known environment limits.

## Implement and falsify

The writer makes the smallest complete change, adds behavior regressions that fail
without it, updates affected docs/specifications, and runs focused checks. Avoid
unrelated cleanup, speculative abstractions and a second progress record.

The reviewer traces correctness, security, compatibility, scope, test gaps and
unnecessary complexity. A no-findings result still states inspected surfaces and
unverified limits. The verifier starts with the narrow regression, runs required
repository gates, and uses a clean/package environment for installation or release
claims. Report actual commands, exits, failures, skipped checks and environment limits.

Return blockers and required corrections to the sole writer. After any change, renew
affected review and verification against the actual bytes, including uncommitted work;
old results cannot establish a new revision passed. Do not waive required failures.

## Deliver the supported result

Map acceptance criteria to implementation and evidence. Inspect the final diff for
unrelated work; reconcile docs/specifications with behavior. Completion requires no
unresolved review blocker and passing required checks or precisely disclosed unavailable
gates. Structural OpenSpec validation alone does not prove implementation correctness.

Return the user outcome, changed components, source identities, independent findings
and disposition, exact checks, remaining limits, recovery notes, issue linkage and
actual branch/PR status. Keep the next engineer's starting point clear.

Commit, push, PR creation, issue updates, merge, release and branch deletion follow the
user's distinct permissions and repository requirements. Prepare a reviewable packet;
do not imply publication or merge from a prepared diff, passed tests or an archive.
