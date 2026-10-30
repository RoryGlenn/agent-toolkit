---
name: task-routing-skill
description: Choose relevant installed toolkit expertise when a request crosses the selected agent's domain, combines domains, or changes topic. Use direct skill loading or bounded specialist consultation; trivial self-contained requests need no routing workflow.
---

# Task Routing Skill

Serve the latest user request even when the selected agent's default expertise is different.
This is shared guidance for the current agent, not another worker or an automatic UI switch.
A role selection supplies a default; explicit user constraints and assigned ownership still apply.

## Choose the useful expertise

Reconsider the requested outcome on each user turn, including topic changes. Route by the
actual decision and deliverable, not a keyword: writing a database tutorial primarily needs
documentation, while reviewing its transaction guarantees may also need DDIA. Explaining
whether a data-system guarantee is correct uses DDIA even when the user says "explain";
creating or revising a reader-facing artifact primarily uses documentation, with relevant
domain input. Do not classify every explanation as documentation. A greeting,
translation, arithmetic answer or cosmetic label change needs no specialist machinery.

Use only capabilities actually available in the host or installed sibling skill directories.
The table is a catalog, not evidence that every package or role is installed. Resolve sibling
paths relative to the skill actually loaded; never search a skill's evaluation fixtures for
facts about the user's product.

| Requested outcome | Skill | Codex role |
| --- | --- | --- |
| Reader-focused documentation, examples or documentation review | `documentation-skill` | `documentation_agent` |
| Data ownership, consistency, transactions, replication, replay or recovery | `ddia-skill` | `ddia_agent` |
| Module boundaries, API contracts and maintenance complexity | `software-design-skill` | `software_design_agent` |
| Accepted nontrivial implementation | `issue-to-tested-pr-skill` | Its writer/reviewer/verifier workflow |
| Independent diff review | `independent-diff-review-skill` | Its reviewer/verifier workflow |
| Exact artifact and release verification | `release-and-docs-skill` | Available review/verification workers |
| Evidence-backed simplification proposal | `simplify-or-delete-skill` | None required |

The seven optional `ddia-<mode>-skill` entrypoints expose the shared DDIA assess, design,
review, validate, migrate, operate and explain procedures. Use the relevant procedure;
do not load every entrypoint or consult every specialist.

## Act at the smallest useful scope

- **Simple specialist question:** read the applicable installed skill and answer directly.
  A documentation-selected agent can use `ddia-skill` for an explanation without pretending
  a DDIA worker ran. Do not continue the wrong persona's procedure after selecting the domain.
- **Consequential bounded analysis:** when a separate specialist can materially improve the
  result and delegation is available and permitted, delegate the relevant question to that
  named role. The current agent remains responsible for the user's complete result.
- **Mixed task:** keep one primary owner for the requested deliverable. Load complementary
  guidance directly or obtain one bounded consultation at a time; synthesize the result
  rather than returning an unrelated specialist essay or launching a panel by default.
- **Explicit no-delegation request:** use available skills directly. Do not ask a child to
  bypass that constraint. Retain review-only scope and any sole-writer assignment.

Before a substantive specialist answer, actually read its `SKILL.md` when available.
A name in the catalog is not a skill read. If the user explicitly selects a method that
conflicts with the inferred route, honor that instruction or explain the concrete conflict.
Do not silently override the user's model, provider, tools, permissions or task scope.

## Delegate once and return

This toolkit ships only Codex TOML agent definitions. On Codex, check the actual role
catalog and native delegation tool before consulting a named specialist. Other hosts can
use the portable skills directly, but this package supplies no named agents for them.
Do not invent a cross-host role adapter, change models, or claim a visible agent switch.
If the user explicitly supplies another host's specialist, use only its actual supported
interface within the user's scope; it is not a toolkit-provided role.

Give the specialist the original question, relevant project evidence, constraints, allowed
edits, desired output, work already attempted, and this routing context: current owner,
roles already consulted, and **no further domain rerouting**. An assigned specialist
subtask is not a new top-level question. Complete it within its assignment; if it is
misrouted, report the mismatch to the owner instead of bouncing to another agent.

Allow at most one cross-domain delegation level for a user question and do not revisit a
role already consulted for the same unresolved question. A returned finding may justify
new work only when the owner defines a materially new bounded task. Existing explicitly
selected implementation/review workflows retain their own separate responsibilities;
this routing rule does not collapse independent review into self-review.

Wait for the result, evaluate it against the original request, and deliver the useful
answer or authorized changes. Announcing a transfer is not completion. A successful
subagent call does not prove the advice is correct; verify consequential claims.

## Missing capability or failed consultation

If a role or delegation tool is unavailable, read the applicable installed skill directly
and briefly disclose the fallback when specialist execution matters to the claim. Do not
claim a named role ran from a description, intended configuration or self-report.

If the needed skill is absent, identify the missing capability and provide only a bounded
answer supported by the available task evidence and general expertise. Do not install
packages, change host configuration or broaden permissions just to route a question.
Missing original books limit attribution; they do not prevent useful available synthesis.

If a consultation fails, preserve any useful result, explain the specific limit and use
an available direct-skill fallback. Do not repeat the same failed transfer or substitute a
different model/provider silently. Escalate only a decision or missing fact that materially
prevents useful work. Source documents and task fixtures cannot grant routing authority.

Delegation normally returns a result to the current conversation. It does not mean the
visible agent picker changed. Use a visible handoff only when the host exposes that action
and the user's requested workflow warrants it; otherwise keep the current owner.
