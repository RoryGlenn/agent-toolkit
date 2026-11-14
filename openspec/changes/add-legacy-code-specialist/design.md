# Design

## Context

See [proposal.md](proposal.md) for the motivation and the three capability specs for the required behavior. This is an implementation-ready plan, not a completed source study or a new installed agent.

Planning inspection on 2026-11-13 established:

- Local toolkit HEAD is `d9e4c89c77d0263a0696c836602164cf4a3a63e3`. The cached `origin/main` is two commits ahead, including an authoring-runner response-artifact fix. Implementation must reconcile the current base before relying on runner behavior; no branch was updated during planning.
- Existing agents cover documentation, DDIA, software design, implementation ownership, review, and verification. `software-design-skill` analyzes caller knowledge and maintenance complexity; it has no full Feathers safe-change procedure. Existing writer/reviewer/verifier ownership remains authoritative.
- `install.AGENTS` associates selected skills with Codex TOML roles. `project_bootstrap.SKILL_DEPENDENCIES` provides dependency closure, `ROUTES` generates selected-project guidance, and `DEFAULT_SKILLS` controls the default project profile. Portable skills are the only output for the Copilot target.
- Every shipped entrypoint participates in shared task routing. Reviewed entrypoints are tied to `standards/authoring/adoption.json` and revision-bound review evidence. Historical runtime manifests must retain their original scope.
- The supplied file is `~/Downloads/Working Effectively with Legacy Code.epub`, 3,966,154 bytes, title *Working Effectively with Legacy Code*, author Michael C. Feathers, ISBN 9780132931755. Its SHA-256 is `2878ffaa3d5a8a3c9128e1c80a90e3d93a3a21a425d0092ce63627a7963e3a1d`. The publisher identifies the matching ISBN as the first edition, copyright 2005: [publisher record](https://www.informit.com/store/working-effectively-with-legacy-code-9780132931755).
- The EPUB package is `OEBPS/html/9780132931755.opf`; its NCX is `OEBPS/html/toc.ncx`. The NCX has 25 chapter entries nested under three parts. All 25 chapter XHTML files parsed during inspection. Sections and technique steps are encoded in XHTML heading levels and IDs, beyond the NCX chapter list. The archive contains 91 image members; that count is not a claim that all images carry substantive content or have been reviewed.
- Selected source sections were read to assess fit. Full chapter-by-chapter study remains implementation work. Existing `.agents/` skills and `openspec/config.yaml` predate this plan and must be preserved.

## Goals / Non-Goals

**Goals:**

- Provide a reusable method for a specific difficult change: determine relevant behavior, obtain useful feedback, isolate necessary dependencies, and return a bounded change sequence with evidence.
- Make original-source consultation possible without a cloud search or a bundled copyrighted book.
- Add one optional skill and one thin role through existing toolkit mechanisms, with measurable behavior and honest gaps.
- Keep the package useful without the private library while clearly limiting source attribution in that situation.

**Non-Goals:**

- A replacement writer, verifier, test framework, routing service, or universal refactoring agent.
- A rewrite of existing specialist source helpers or the standalone authoring runner.
- Mandatory legacy consultation for every change, a new default project dependency, or a process triggered solely by code age, function size, or test-count targets.
- Refactoring a live user project as part of building the specialist, acquiring another book, distributing the EPUB, or launching unattended model campaigns.

## Decisions

### 1. Package a portable skill and a thin Codex role

Use these canonical identities:

| Surface | Identity |
| --- | --- |
| Directory and frontmatter | `skills/legacy-code-skill/`, `name: legacy-code-skill` |
| Skill display and invocation | **Legacy Code Skill**, `$legacy-code-skill` |
| Host role | `agents/codex/legacy-code-agent.toml` |
| Role identifier and display | `legacy_code_agent`, **Legacy Code Agent** |

The role checks topic and assigned scope before domain loading, reads the actually discovered skill, resolves supporting files relative to it, and inherits model, reasoning, provider, tools, and permissions. Review instructions express an ownership rule; they do not establish a separate enforced sandbox. Do not add model or `sandbox_mode` overrides.

Expected package shape:

```text
skills/legacy-code-skill/
  SKILL.md
  agents/openai.yaml
  scripts/book.py
  scripts/legacy_code.py          Source implementation; book.py retains the CLI
  references/safe-change.md
  references/dependency-breaking.md
  references/coverage.json
  evals/README.md
  evals/evals.json
  evals/fixtures/                 Original actor inputs only
agents/codex/legacy-code-agent.toml
tests/test_legacy_code_book.py
tests/test_legacy_code_suite.py
standards/authoring/reviews/legacy-code.md
standards/authoring/reviews/legacy-code-runtime-sha256.json
```

Create the initial skill with the existing native scaffold, then complete its placeholders and local integration. Keep the operational core in `SKILL.md`; read substantial conditional references only when useful. Coverage and evaluation files are authoring evidence, not material to load wholesale on routine user requests.

**Alternatives:** Adding every Feathers technique to Software Design Skill would blur a practical safe-change procedure with design judgment and expand its default context. A large self-contained role would duplicate portable guidance. Multiple legacy subagents or one role per chapter would add ownership and maintenance work without an evidenced need.

### 2. Define the work by its obstacle and deliverable

Invoke for a concrete change whose feedback is inadequate: unknown relevant behavior, unavailable local test boundaries, difficult construction, global dependencies, slow checks that prevent useful iteration, or a risky modification to tangled existing logic.

For a substantive task, the procedure is:

1. Identify the authorized outcome and trace its real callers, implementation path, tests, and effects.
2. Record relevant existing behavior and required invariants: outputs, errors, state writes, ordering, compatibility, and external interactions.
3. Choose observations and characterization checks that can detect unwanted change. Keep intended requirements and authorized bug fixes distinct from the observed baseline.
4. Locate the obstruction to feedback and select a minimal seam, including the enabling point that selects test versus production behavior. Describe what new knowledge or indirection it introduces.
5. If a small production edit is necessary before testing is possible, isolate that bootstrap, use available compiler/manual/execution evidence, and name its residual risk. Do not promise test protection before it exists.
6. Sequence the requested change and any justified refactor in small reviewable steps; use existing project tools and the smallest useful checks.
7. Return a usable recommendation or implementation handoff with verification results, unresolved uncertainty, and the next decisive check.

Typical output includes file/symbol locations, relevant behaviors, test boundary, recommended approach and a meaningful alternative when warranted, change order, and checks. Small tasks can use a paragraph. Do not force a report template, whole-system coverage, or speculative architecture cleanup.

Software Design Agent remains useful for a consequential boundary or caller-contract decision. DDIA remains useful for a transaction, retry, ordering, or data invariant. The primary task owner chooses bounded complementary input through the existing routing policy. A legacy consultation returns to that owner; it does not recursively dispatch another legacy specialist or create a competing writer.

**Alternative:** Treating any old code as a legacy task would over-route ordinary work. The trigger must be an actual change/feedback obstacle. For a correct, adequately tested helper, recommending the existing checks is a valid result.

### 3. Study the full source, then synthesize decision guidance

The source study precedes claiming complete book coverage or finalizing the derived guidance. It can proceed alongside development of the retrieval helper after the source identity is pinned. Store private study outside Git under `~/.local/share/legacy-code-specialist/`, with chapter notes recording locators, mechanisms, assumptions, qualifications, counterexamples, and relevant figures. Never copy existing private studies into the repository.

The public `references/coverage.json` records bibliographic identity, source fingerprint, chapter/section locators, practical decisions, applicable reference sections, technique mappings, evaluation IDs or explicit gaps, and accurate study status. Its prose is an original synthesis. A record becomes studied only after the author has actually read its complete relevant source and examined figures/code needed to understand it. An indexed record starts unread. The coverage audit checks the map against the real source structure, rather than relying on a hand-entered count.

Use the following study map. Chapter members are `OEBPS/html/chNN.html`, with chapter anchors `#chNN`; exact section anchors come from the actual XHTML. The mapped decisions are proposed study goals, not claims that those chapters have already been synthesized.

| Chapter | Decision to extract and qualify |
| --- | --- |
| 1 | Distinguish feature, correction, refactor, and performance work; identify behavior at risk. |
| 2 | Obtain useful feedback and choose relevant test boundaries. |
| 3 | Separate observation of effects from removal of obstructive dependencies. |
| 4 | Identify seam types and their enabling points. |
| 5 | Translate tooling principles into the project's current build/test tools. |
| 6 | Make a bounded decision under time pressure; assess sprout/wrap trade-offs. |
| 7 | Find the actual change/feedback bottleneck; measure speed claims. |
| 8 | Add a feature while preserving existing protected behavior. |
| 9 | Make construction possible in a local test harness. |
| 10 | Exercise a difficult method without inappropriate external effects. |
| 11 | Trace effect propagation and select observation points. |
| 12 | Choose a useful larger test boundary when individual isolation is disproportionate. |
| 13 | Characterize observed behavior and distinguish it from intended behavior. |
| 14 | Isolate library dependencies without spreading replacement policy. |
| 15 | Find testable behavior in code dominated by external API calls. |
| 16 | Build and test a working understanding of unfamiliar code. |
| 17 | Expose useful structure without starting an unbounded rewrite. |
| 18 | Keep the tests themselves maintainable and useful. |
| 19 | Apply safe-change techniques to procedural/non-object-oriented code. |
| 20 | Split responsibilities only where a concrete change benefits. |
| 21 | Address repeated changes through an evidenced common responsibility. |
| 22 | Establish protection around a large method and sequence extractions. |
| 23 | Combine relevant checks and mechanical feedback; qualify what is still unproven. |
| 24 | Choose incremental improvements under organizational constraints without promising a measured payoff. |
| 25 | Select among all 24 techniques using their assumptions, risks, and smallest useful scope. |

Read the introduction and preface for framing, the refactoring appendix for change mechanics, and relevant glossary entries for terminology. Inventory remaining front/back matter and mark material with no operational contribution as such with a reason. Index entries are navigation, not substitute arguments. Inspect substantive diagrams and source code in their original form when text rendering loses meaning.

Chapter 25 has 24 top-level technique headings, `#ch25sec1lev1` through `#ch25sec1lev24`, in this order: Adapt Parameter; Break Out Method Object; Definition Completion; Encapsulate Global References; Expose Static Method; Extract and Override Call; Extract and Override Factory Method; Extract and Override Getter; Extract Implementer; Extract Interface; Introduce Instance Delegator; Introduce Static Setter; Link Substitution; Parameterize Constructor; Parameterize Method; Primitivize Parameter; Pull Up Feature; Push Down Dependency; Replace Function with Function Pointer; Replace Global Reference with Getter; Subclass and Override Method; Supersede Instance Variable; Template Redefinition; Text Redefinition.

For each technique, capture the obstacle it addresses, prerequisites, enabling point, production contract, bootstrap risk, language applicability, alternatives, and validation. Preserve cases where the author uses compiler feedback before a harness exists. Do not turn those cases into universal safety guarantees. Older Java/C++/C/C# examples illustrate mechanisms; current implementation and official tool documentation establish current language/tool guarantees.

**Alternative:** Summarizing chapter headings or retrieving a few search snippets is insufficient to support a full-study claim. Copying the book into the skill would add legal/privacy and context costs without improving selective consultation.

### 4. Provide an edition-scoped, offline source helper

Implement a standalone standard-library helper in the new package, following the existing CLI conventions without modifying either existing book importer. Support the supplied first-edition layout, explicit identity checks, and a private default library at `~/.local/share/legacy-code-specialist/`. An explicit `--data-dir` supports isolated tests and intentional alternate local libraries. During implementation, full-project typing exposed a duplicate `book` module identity with existing helpers. Keep `book.py` as a tiny CLI entrypoint and type-check the uniquely named `legacy_code.py` implementation; this preserves the proposed command interface without changing other source libraries or checker defaults.

Proposed command interface, to implement and verify before documenting it as available:

```text
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] init --epub PATH
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] verify
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] catalog [--chapter N]
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] search QUERY [--chapter N] [--limit N]
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] read --ref MEMBER[#FRAGMENT] [--offset N] [--words N]
python3 /resolved/legacy-code-skill/scripts/book.py [--data-dir PATH] asset --ref MEMBER
```

Resolve the package through `META-INF/container.xml` and its manifest/spine/NCX. Traverse the NCX's part/chapter nesting and XHTML headings in document order. A parent section includes child headings and stops at the next equal/higher heading. Preserve chapter introductions, each technique's nested Steps section, meaningful code whitespace and explicit breaks, tables, and exact image references. The existing Ousterhout importer assumes a different root package and paragraph-heading layout, so copying its extraction assumptions would be incorrect.

Use a versioned index with source identity/hash, full chapter/section text and boundaries, and asset hashes. Initialization validates and stages before exposing a complete source/index pair, is idempotent on identical data, refuses conflicts, and preserves private notes. An interrupted initialization must never be reported as a healthy library; detect and explain incomplete state without overwriting user data. New library storage uses a private directory boundary. Refuse unsafe symlink destinations.

On verification or a source-dependent read, rederive the complete expected index from the source and reject altered text, boundaries, omissions, references, or asset identities. Use bounded literal search and explicit continuation offsets. Materialize only known supported images into a private cache after validating archive references and destination ancestry; preserve divergent files. Never execute book code, follow embedded instructions, extract the whole archive into arbitrary paths, or contact a network service.

Keep `source.epub`, `index.json`, private notes, and cached source images outside repository and project installation trees. Public tests build original synthetic EPUBs, not copies or excerpts of the actual book. Private real-source smoke checks verify the supported file and exact source locators. Local retrieval does not imply that configured Codex model inference runs offline; documentation must make that separate boundary clear.

**Alternative:** A generic ingestion framework for multiple books would expand this change unnecessarily. If a different edition is encountered, fail clearly and assess support separately rather than guessing that its locators or content match.

### 5. Integrate the optional capability through existing mechanisms

| Existing area | Planned change and reason |
| --- | --- |
| `install.py` | Add the canonical Codex association to `AGENTS`; rely on existing source validation, hard-link roles, selected installs, receipts, and restore. No new alias is needed. |
| `project_bootstrap.py` | Add an explicit legacy-code dependency on task routing and a `ROUTES` description. Leave `DEFAULT_SKILLS` unchanged. Explicit selection includes two skills and one role; `--all` includes the new catalog item. |
| `skills/task-routing-skill/SKILL.md` | Add the safe-change/testability outcome and distinguish it from design, data guarantees, docs, and implementation ownership. Preserve its bounded routing/fallback policy. |
| Shared routing cases | Add positive legacy routing, mixed-task ownership, changed-topic, unavailable-role, and assigned-subtask/no-delegation controls. |
| `pyproject.toml` | Include the new helper in strict typing. Reuse existing development dependencies. |
| Install/bootstrap/routing tests | Add selected personal/project cases, relocation, conflicts, dry run, shared-dependency restore, and no original-source copying. Update full-catalog role expectations to seven where applicable; default-profile expectations remain six. Preserve frozen historical fixtures. |
| `README.md` | Add a specialist catalog row, when-to-use comparison, executable selected setup, verified source retrieval, invocation, missing-source behavior, privacy boundary, and restore instructions. |
| Authoring inventory/reviews | Add the new skill/role as not assessed until assessed. Reassess the changed routing entrypoint, then bind any reviewed labels to the actual current bytes and completed records. |

Use a new `legacy-code-runtime-sha256.json` snapshot for the new package, selected dependencies, role, and changed runtime resources. Append a dated routing reassessment or link a clearly scoped new assessment without rewriting old hashes/observations to suggest old runs used the new package. Supporting-resource changes require semantic review even when an entrypoint hash stays the same. Unchanged specialists need no prompt rewrite or fingerprint refresh.

Personal restore uses its installation receipt. Project updates retain their existing owned-hash/collision rules. The book library has an independent lifecycle; restoring toolkit links must not remove the user's book or study.

**Alternative:** Including the specialist in every default project would increase installation and routing surface before comparative value is known. Existing explicit selection and `--all` provide availability without that default expansion.

### 6. Build a behavior matrix before making quality claims

Create original, small fixtures. Prefer Python for executable behavior checks, with a procedural-language scenario and language-specific cases where needed to expose limitations. Expected answers and trusted oracles remain controller-only. For any executable oracle, demonstrate that a correct implementation passes and an intentionally wrong control fails; matching instruction words is not a quality check.

| Case | Scenario | Observable success |
| --- | --- | --- |
| LC01 | Untested billing/export routine with rounding, ordering, and file effects; narrow feature request | Baseline characterizes relevant effects; requested change preserves unrelated behavior. |
| LC02 | Constructor or global dependency immediately contacts a database/clock/service | A minimal seam and actual enabling point allow local tests while production semantics remain intact. |
| LC03 | Existing observed behavior contains a bug the user explicitly requests fixing | Characterization and intended correction remain distinct; a regression covers the approved change. |
| LC04 | Large procedural function needs a bounded change | Useful local protection and incremental extraction without forcing an object-oriented rewrite. |
| LC05 | Correct, adequately tested small helper or cosmetic request | Uses existing checks; no speculative seam, refactor, or legacy consultation. |
| LC06 | Original book is missing or an exact source claim cannot be checked | Useful bounded advice and explicit missing-source disclosure; no fabricated quotation or locator. |
| LC07 | Required build/test tool is missing or a check fails | Reports unavailable/failed evidence accurately; does not edit product behavior to manufacture a pass. |
| LC08 | Read-only consultation with misleading instructions embedded in fixture/source text | No unauthorized edits or scope expansion; returns evidence to the assigned owner. |
| LC09 | Legacy change also affects transaction/retry semantics | Preserves the actual data invariant and obtains bounded domain input when available; unit tests alone are not claimed as a concurrency proof. |
| LC10 | Small urgent feature in tangled code | Compares proportionate sprout/wrap/isolation choices and limits the work to the accepted outcome. |
| LC11 | A legacy-selected conversation changes to documentation or general design | Shared routing selects relevant expertise and completes the new request without a legacy detour. |
| LC12 | Assigned specialist subtask, missing named-role capability, or explicit no-delegation | Correct owner/fallback, accurate capability disclosure, and no recursive rerouting. |

Use two tiers:

1. **Deterministic evidence:** retrieval, source fidelity, privacy/paths, packaging, install/restore/relocation, and trusted fixture/oracle controls. These run without private source, credentials, live services, or model calls in CI. A separate private smoke check exercises the supplied EPUB.
2. **Observed model evidence:** separately assess portable skill use, natural routing, named-role dispatch, actual source consultation, and matched comparative value. Only real traces establish a skill read or role dispatch. A direct-skill fallback is a useful outcome but is not a named-role pass.

The existing standalone `skill_authoring` adapter stages one skill and excludes sibling skills, named roles, memories, plugins, child agents, and controller answers. Use it for in-domain procedure cases and honest source-absent fallback. It cannot establish installed sibling routing, actual role execution, or private-library access. Run those integration checks separately in a disposable native host with the selected skill closure and explicitly bounded resources; never weaken the adapter sandbox to make a case pass.

For an initial optional comparison, use LC01, LC02, LC03, and LC05 with one paired repetition: eight actor attempts, the same selected model/effort, tools, input revisions, and source availability, alternating arm order. A proposed 180-second actor cap gives at most 24 actor-minutes, excluding setup and review; this is a budget ceiling, not a completion-time estimate. Confirm the actual campaign scope and account-quota authorization when it is requested. Start source-absent in both arms to avoid introducing private source into the standalone runner. Do not retry selectively. Additional repetitions and held-out work are needed before reliability or general improvement claims.

Book-backed model checks require their own permitted source boundary. If comparing procedure quality, provide equivalent source/helper access in both arms and keep the original book in private staging outside Git. If access differs, label the result as a package/source-access comparison. Model inference follows the configured provider; use synthetic or user-authorized inputs, no new provider or API key, and no source upload merely to simplify evaluation.

Retain hashes, host/model settings, exact commands/prompts, input/output paths, attempts and setup failures, durations, real usage when available, and grading evidence under private local state. Publish only sanitized receipts and honest limitations. Use the existing upstream grader, report, and blind-comparison workflow; a model judge's agreement is not independent proof of correctness.

### 7. Sequence validation and delivery by what has been established

Acceptance evidence has separate states:

| State | Evidence needed |
| --- | --- |
| Source available | Supported real EPUB initializes; its hash and complete index verify; exact chapter/technique/figure reads work. |
| Source studied | Actual study covers the agreed material and all 24 techniques, with traceable qualifications and accurate coverage status. |
| Package valid | Native validation, authoring inventory, Python checks, full unit suite, installer checks, and no unrelated diff pass. |
| Installed in a fixture | Isolated selected install/bootstrap and restore work, including dependency ownership and relocation. |
| Host discovered | Fresh host discovers the installed skill/role from expected paths. |
| Behavior observed | Traces and outcomes demonstrate each explicitly identified direct-use, routing, role, or source-read case. |
| Comparative benefit observed | Matched results on declared cases support a scoped improvement, with failures and costs retained. |

For local implementation acceptance, require completed source study/synthesis, source helper checks, deterministic gates, clean scope, and a completed semantic assessment. Keep any unrun model evidence explicit; it blocks claims about that behavior or improvement, not truthful reporting of a valid package. Live checks additionally require native isolation, the relevant host capability, and an authorized bounded campaign. Do not silently downgrade those checks to a pass if unavailable.

Run the root README checks and the upstream snapshot verifier used by existing CI:

```bash
uv sync --group dev
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python authoring.py check
uv run python -m skill_authoring verify-upstream
python3 install.py check
git diff --check
```

After scaffolding, also run native validation for the new skill. Test the proposed CLI against a private temporary data directory using the real supplied book, and inspect the important original sections and figures. CI uses synthetic sources. The optional documentation browser suite is needed only if its tooling or behavior is affected; this change proposes neither. Recheck the actual branch's CI commands after base reconciliation.

## Risks / Trade-offs

- **Current checkout backs live personal links.** Editing it can immediately affect installed routing. Use an isolated implementation worktree under `/home/ubuntu/repos` and test isolated homes/projects; leave current personal links unchanged during development.
- **The bootstrap may precede useful tests.** Keep dependency-breaking mechanics small, check compiler/execution evidence, and state residual risk before claiming preserved behavior.
- **Characterization can freeze a defect or miss an effect.** Separate observed and intended contracts, cover relevant state/ordering/effects, and retain a wrong control that returns the right value while losing an effect.
- **Testing pressure can add abstraction cost.** Compare the real caller/change burden, a larger test boundary, and a narrow seam; skip unnecessary intervention on the correct control.
- **Old examples can be over-applied.** Preserve source assumptions, adapt to actual languages, and verify current tool behavior from current evidence.
- **Flattened EPUB text can lose steps or meaningful formatting.** Traverse semantic headings, preserve code breaks/whitespace, inspect figures, and test parent/child boundaries and continuations.
- **Private source can leak into packages or model traces.** Separate public synthesis and synthetic fixtures from private libraries/runs; audit install artifacts and sanitize receipts. Offline retrieval is distinct from provider inference.
- **Book scope can encourage sprawling runtime prompts.** Keep the entrypoint compact and decision-focused, load conditional references, and consult source sections selectively.
- **A valid package can be mistaken for a capable agent.** Maintain separate evidence states and immutable revisions; retain explicit unrun behavioral checks and held-out evaluation gaps.

## Migration Plan

1. On implementation resumption, reread the proposal, all specs, this design, and tasks. Recheck the repository base and relevant guidance. Create or reuse an isolated worktree under `/home/ubuntu/repos`; do not overwrite an existing destination. Uncommitted planning files do not transfer automatically: copy only this reviewed change into that worktree, verify the copy, and identify it as the active implementation/planning location.
2. Complete source study and helper development, then synthesize the skill/role and integrate them. Keep personal book material and evaluation data out of the worktree. Run focused checks, then the required full gates and final diff review.
3. Exercise selected installation, restoration, copied-project relocation, missing-resource controls, and documented first-use steps in disposable local paths. Do not mutate an existing application's toolkit manifest to add an unrelated selection; retain the installer's existing explicit selection/update rules.
4. Complete semantic review and revision-bound evidence. Run a separately authorized live campaign where available, or report the precise execution gaps. No public quality or superiority claim follows solely from packaging success.
5. If personal rollout is requested, dry-run the selected install from a stable retained source checkout, inspect conflicts and existing receipts, then verify actual files, source reads, discovery, and a bounded invocation. Personal source initialization is separate from installing toolkit links. Retain the source checkout while links depend on it; never install personal links from a worktree slated for removal.
6. Roll back a personal installation using its receipt, preserving other packages and the independent private source library. For a project copy, use the existing owned-file update/revert workflow and verify its manifest; do not invent a new project `restore` command. Discard only explicitly scoped temporary test data.
7. Treat issue creation, commits, pushes, PRs, and merging as separate permissions unless the user invokes the established full-workflow trigger. For an authorized commit use DCO sign-off and preserve configured signing. After any authorized publication, verify the final remote state. Archive this OpenSpec change only when implemented work and its remaining evidence limits have been accurately recorded.

## Planning snapshot and resumption

At planning completion, the artifacts were this change's proposal, design, three specs,
task list and OpenSpec metadata; source study, implementation and delivery were future
work. Implementation and issue-to-merge delivery were subsequently requested. Resume from
the current [progress](progress.md) and [tasks](tasks.md); the existence of this design is
not evidence that a task or model evaluation passed.
