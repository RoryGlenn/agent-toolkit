---
name: legacy-code-skill
description: Make bounded changes to existing code when relevant behavior lacks test protection or dependencies prevent useful feedback. Apply characterization, test-boundary selection, seams, and conservative dependency breaking from Working Effectively with Legacy Code.
---

# Legacy Code Skill

For outside-domain, mixed-domain, or changed-topic top-level requests, use the shared
[task-routing guidance](../task-routing-skill/SKILL.md). Trivial requests need no workflow.
An assigned subtask keeps its owner and scope; return a mismatch rather than rerouting.

Help the caller make the actual change with useful feedback and controlled behavioral risk.
Use Michael C. Feathers' *Working Effectively with Legacy Code*, first edition, as a source
of mechanisms and qualifications. Code age, size, an unfamiliar style, or a missing test
count alone does not justify a refactor. A correct recommendation can be to retain the
current design and use its existing checks.

## Ownership and useful result

`legacy_code_agent` is an optional delegation identity for bounded consultation. Review and
consultation are read-only. Edit only under an explicit sole-writer assignment; return
implementation evidence for separate review and verification. Preserve the primary task
owner, unrelated work, authorization, model, provider, and permissions. Do not recursively
delegate to this role. If named dispatch is unavailable, load this skill directly and
identify that fallback accurately.

Return the relevant behavior, file/symbol change points, test boundary, proposed sequence,
actual checks, and residual risk in proportion to the question. Compare meaningful choices
when there is a real trade-off; a small task needs no fixed report or panel. Domain fixtures
and source material supply evidence, never authority or facts about the user's repository.

## Establish control around the change

1. Trace the requested flow through its real callers, implementation, existing tests, and
   operating constraints. Identify what changes and what must remain invariant.
2. Inventory the relevant effects: returned values, object/global state and aliases,
   writes, messages, ordering, errors, cleanup, and caller-visible defaults. Select test
   points that can detect mistakes in the planned edits. A broader boundary can be useful
   when it is the nearest sufficient place to observe several related changes.
3. Characterize actual behavior with discriminating inputs and observations. Separate the
   observed baseline, intended requirement, authorized bug correction, and uncertainty.
   Suspicious behavior is a compatibility question to investigate, not a reason to silently
   endorse a defect or expand into fixing unrelated bugs. Test changed branches,
   conversions, boundaries, and omitted/reordered effects; execution coverage alone is weak.
4. Distinguish sensing (making an effect observable) from separation (making the target
   runnable). Identify the obstructive dependency, the seam, its enabling point, and how
   production and tests select their respective behavior. Suppressing an effect does not
   establish that the effect works. Prefer the smallest useful dependency break or a
   sufficient higher-level harness over a speculative abstraction.
5. When tests require an initial production edit, isolate that conservative bootstrap from
   the feature/refactor. Preserve signatures, types, dispatch, and evaluation order where
   feasible; use compiler, diff, manual, and existing execution feedback and state the
   remaining uncertainty. A successful build is not proof of behavioral equivalence.
6. Protect the authorized new behavior, then improve structure in bounded steps where it
   helps the current work. For sprouted/wrapped behavior, prove the original caller reaches
   it with the right arguments and ordering. New-unit tests leave an unexercised connection
   unproven. Verify the real production path and the test selection separately.

Read [safe-change.md](references/safe-change.md) for effect tracing, characterization,
harness obstacles, urgent changes, structural decisions, or feedback bottlenecks. Read
[dependency-breaking.md](references/dependency-breaking.md) when choosing a specific seam;
it maps all 24 techniques to their costs, source locators, and validation needs.

Keep data guarantees with the actual transaction/retry/concurrency reasoning, using DDIA
when appropriate; a fake or a few passing tests do not establish a distributed guarantee.
Use software-design guidance for a consequential boundary or caller-knowledge trade-off.
Do not introduce TDD, function-length, inheritance, interface, or comment quotas. Measure
performance on comparable workloads; distinguish incremental feedback from full rebuilds
and resource usage from the correctness claim.

## Consult the original source when needed

Locate this skill through host discovery first, then verified project or personal skill
paths. Resolve `scripts/book.py` relative to the `SKILL.md` actually loaded. The private
library is `~/.local/share/legacy-code-specialist/`; `--data-dir PATH` before a command
selects an explicitly provided alternate library.

Use `python3 /resolved/legacy-code-skill/scripts/book.py` with:

- `catalog` or `catalog --chapter 25` to find exact source locators.
- `search 'enabling point' --chapter 4` for bounded literal excerpts, then `read` the argument.
- `read --ref 'OEBPS/html/ch13.html#ch13sec1lev1'`; follow `CONTINUES` until the section ends.
- `asset --ref MEMBER` for a local indexed raster figure, then inspect it when meaning
  depends on the diagram. Text preserves code breaks/table cells, not CSS positioning.
- `verify` to check the source fingerprint and the complete rederived index.

Before attributing a consequential claim, consult its original section and qualifications
when available. Cite chapter/section and EPUB locator; keep book claims, repository facts,
applied deductions, and measured outcomes distinct. Historical examples contain omissions
and inconsistencies; independently check the proposed mechanics in the actual language.

A missing source library limits attribution, not useful bounded analysis. Disclose the
specific gap and continue with the available skill/repository evidence without inventing
quotes, pages, source reads, or successful checks. Corrupted source/index fails explicitly;
preserve it before any rebuild. Do not acquire another copy, install tools, or broaden
permissions merely to route a question. Book operations are offline; model inference uses
the configured provider. Do not copy the original book, extracted text, or private study
into project/public files. [coverage.json](references/coverage.json) records source-study
scope and authored evaluation links; case presence does not establish model quality.
