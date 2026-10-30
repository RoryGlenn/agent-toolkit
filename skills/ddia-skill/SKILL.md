---
name: ddia-skill
description: Apply DDIA across data-system architecture, storage/models, evolution, replication, transactions, batch/stream processing, recovery, and data consequences. Use for consequential data decisions, implementation guidance, reviews, or explanations.
---

# DDIA Skill

Improve the actual engineering decision using *Designing Data-Intensive Applications*,
Second Edition. Start with the repository, workload, business invariants and failure
model. Prefer the simplest sufficient design; additional distribution and components
need evidence. Keep routine tasks proportional.

## Select a procedure and relevant concepts

Read [the common decision process](references/decision-process.md), then the procedure
matching the task. Seven callable `ddia-<mode>-skill` packages expose these same modes;
their installer dependency includes this shared skill.

| Task | Procedure |
| --- | --- |
| Is this mechanism worth building? | [Assess](references/workflows/assess.md) |
| Architecture or project creation | [Design](references/workflows/design.md) |
| Specifications, code/diffs, configuration or generated rules | [Review](references/workflows/review.md) |
| Concurrency, failure, load or recovery experiment | [Validate](references/workflows/validate.md) |
| Compatibility, backfill, reprocessing or cutover | [Migrate](references/workflows/migrate.md) |
| Capacity, overload, runbooks, restore or reconciliation | [Operate](references/workflows/operate.md) |
| Conceptual explanation or teaching | [Explain](references/workflows/explain.md) |

Use [topic routes](references/routing.md) or the local helper to locate only relevant
concept clusters across all 14 chapters. Resolve helpers relative to the `SKILL.md`
actually loaded, never an assumed working directory:

```bash
python3 /resolved/ddia-skill/scripts/guide.py route 'offline edits and conflicting writes'
python3 /resolved/ddia-skill/scripts/guide.py topics --chapter 8
python3 /resolved/ddia-skill/scripts/guide.py concept write-skew
python3 /resolved/ddia-skill/scripts/guide.py check
```

The [coverage ledger](references/coverage.json) distinguishes authored guidance, source
locator validation, bounded executable experiments and measured agent behavior. A linked
case or chapter file is not evidence that the agent performs the task correctly.

## Retrieve and qualify source claims

The optional personal source/index is at `~/.local/share/ddia-specialist/`; initialize
it with this skill's `scripts/book.py init --epub /path/to/second-edition.epub`.
Original practical references ship with the skill and work without that source library.
If original source is unavailable, disclose it and avoid claiming source consultation.

Use `book.py catalog --chapter N`, ranked `search QUERY --chapter N`,
`read --ref 'OEBPS/ch08.html#sec_transactions_write_skew'`, and
`neighbors --ref REF`. Search expands selected aliases and permits partial matches;
results and adjacent headings are navigation, not complete arguments or automatically
relevant qualifications. Read the full source and its applicable qualifications.
`read` prints explicit `--offset` continuation. `verify` checks source and index integrity.
`guide.py check --source-index /path/to/index.json` checks every ledger locator and source
fingerprint; it does not establish semantic fidelity.

Distinguish book principle, repository evidence, applied deduction and current product
behavior where consequential. Use real chapter/heading and EPUB locators; never invent
page numbers. Check exact product/version/configuration guarantees against current
official documentation. ACID, quorum, Raft, exactly-once and serverless labels do not
prove an end-to-end guarantee. For layout-sensitive code, tables, equations or diagrams,
inspect original source/assets; text extraction does not interpret images.

## Ownership and handoff

Consult `ddia_agent` for consequential changes to data ownership/model/storage, schemas,
transactions/concurrency, replication/partitioning, message effects, batch/stream pipelines,
recovery, retention or derived state. Supply the task, paths/diff, constraints and decision.
If named-role dispatch is unavailable, use this skill directly or assign a generic worker
that reads it; disclose the fallback rather than claiming named-role dispatch occurred.

The parent retains project and implementation ownership. Consultation/review is read-only;
edit only with explicit sole ownership of the affected implementation. Independent review
then belongs to another agent. Do not recursively delegate to `ddia_agent`.

Use the optional [data contract](assets/data-contract.template.md),
[decision](assets/decision.template.md), and [handoff](assets/handoff.template.md) assets
within existing project documentation when helpful. Translate agreed invariants into
executable checks; advice alone cannot enforce itself or block another agent.

[Evaluation instructions](evals/README.md) describe public cases and controlled comparisons.
Preserve correct controls and penalize unnecessary complexity as well as missed defects.
Validation proves only behavior actually exercised; do not claim production correctness
or agent superiority from source integrity, authored procedures or fixture success.
