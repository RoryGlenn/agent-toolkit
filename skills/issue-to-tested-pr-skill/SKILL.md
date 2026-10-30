---
name: issue-to-tested-pr-skill
description: Take an accepted repository issue or clearly scoped engineering task through one-writer implementation, independent review, verification, and a review-ready pull request. Use for non-trivial features, bugs, refactors, migrations, or architecture work; do not use for unscoped brainstorming or trivial text-only edits.
---

# Issue to Tested PR Skill

Convert one accepted unit of work into independently reviewed, reproducibly verified repository evidence.

## Required inputs

- The issue, task, or accepted requirement.
- The target repository and base branch.
- Repository-local `AGENTS.md` guidance and required validation commands.
- Any explicit scope, risk, compatibility, or release constraints.

If the requirement is materially ambiguous, resolve it from the issue, repository evidence, and existing behavior before editing. Do not invent a broader product decision.

## Operating model

The parent agent is the coordinator. Keep these roles separate:

1. **Writer** — `implementation_owner_agent`, or one designated worker (including the parent) when that custom agent is unavailable.
2. **Reviewer** — `adversarial_reviewer_agent`, read-only.
3. **Verifier** — `verifier_agent`, behavior- and command-focused.

When a named review or verification role is unavailable, assign that responsibility to a separate generic agent. Preserve independence from the writer and give each agent the original requirement and observable artifacts. If the host cannot delegate, complete the useful local checks and report independent review or verification as unavailable; self-review does not satisfy that evidence requirement.

Use only one writer for a change. Do not let two agents edit overlapping source files. Do not start review and verification until the writer has finished the first complete diff.

Use no more than three active engineering lanes. Prefer the Codex Worktree mode for the writer when the local checkout is dirty, another task is active, or isolation materially reduces risk. For manual worktrees, use `codex-lanes` if it is installed; otherwise use the existing Git worktree workflow.

## Workflow

### 1. Establish the contract

- Read all applicable instruction files.
- Read the complete issue or requirement and linked authoritative material.
- State the user-visible outcome, acceptance criteria, non-goals, and evidence needed.
- Identify the smallest responsible change and the likely affected boundaries.
- Record any check that cannot run in the current environment.

Do not treat an issue checklist, generated prose, or an earlier agent summary as proof.

For consequential data changes, consult installed DDIA guidance when available: define authority,
business invariants and data boundaries before implementation; carry the relevant requirements
and falsification checks into the writer handoff. Revisit these when schemas, transaction scope,
replication, message effects, processing or recovery change. Routine unrelated edits need no DDIA
step. Project requirements remain authoritative; recommendations are not automatic merge gates.

### 2. Inspect and reproduce

Before editing:

- Trace the real execution path and current behavior.
- Reproduce a reported defect when practical.
- Identify existing tests, fixtures, specifications, and documentation that own the behavior.
- Check for an existing implementation or duplicate work.

For large or unfamiliar repositories, delegate bounded read-only exploration, then keep only the evidence summary in the parent thread.

### 3. Implement with one writer

Delegate to `implementation_owner_agent` with:

- the exact requirement and accepted scope;
- relevant files and evidence, not the entire noisy exploration log;
- required tests and repository gates;
- explicit instructions to preserve unrelated work.

The writer must:

- make the smallest complete change;
- add regression or behavior tests that would fail without the fix;
- avoid unrelated cleanup and speculative abstractions;
- update affected specifications and documentation when behavior changes;
- report changed files, test commands, residual uncertainty, and any blocked check.

### 4. Review independently

After the first complete diff, delegate to `adversarial_reviewer_agent`.

Give the reviewer:

- the original requirement and acceptance criteria;
- the base and head refs or exact diff;
- relevant repository rules.

Do not lead with the writer's justification. The reviewer should independently look for correctness defects, security problems, scope drift, compatibility breaks, missing tests, and unnecessary complexity.

A review that finds no issues must still identify what was inspected and what remains unverified.

### 5. Verify independently

Delegate to `verifier_agent` after the diff is stable. The verifier must:

- start from the requirement and observable behavior;
- run the narrow regression first, then required repository gates;
- use a clean or packaged environment when the requirement depends on installation, release, or platform behavior;
- report exact commands, exit results, skipped checks, and environment limits;
- avoid changing product source to make verification pass.

Reviewer and verifier may run in parallel only after the writer has stopped editing.

### 6. Resolve findings

- Classify findings as blocker, required correction, or optional hardening.
- Return blockers and required corrections to the single writer.
- Re-run the affected review and verification after changes.
- Do not waive a failing required check merely because the implementation appears reasonable.

### 7. Prepare the PR

The final PR package must include:

- problem and user outcome;
- smallest implemented change;
- files or components affected;
- tests and exact verification results;
- independent review findings and disposition;
- limitations, unrun checks, and rollout or rollback notes;
- issue linkage.

Do not merge, release, publish, or delete branches unless the user explicitly requested that effect and repository policy permits it.

## Completion standard

Work is complete only when:

- acceptance criteria map to implementation and evidence;
- the diff contains no unrelated changes;
- independent review has no unresolved blocker;
- required verification passed or every unavailable gate is stated precisely;
- documentation and specifications match shipped behavior;
- the working tree and PR state are understandable to the next engineer.

## Final response format

Return:

1. **Outcome**
2. **Implementation**
3. **Independent review**
4. **Verification**
5. **Remaining limits**
6. **PR or branch reference**
