# Agent Toolkit

A reusable agentic starting layer for full-stack, frontend, backend, and local software
projects. Bring established engineering workflows and domain expertise into a project's
repository so collaborators can use the same guidance. Each project supplies its own
architecture, stack, package manager, commands, audience, and terminology.

## Start a project

The bootstrap command requires Python 3.11 or newer on macOS or Linux. Run it from an
existing toolkit checkout, targeting a new or existing application directory:

```bash
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project --dry-run
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project
```

The default engineering selection includes `documentation-skill`, `ddia-skill`,
`software-design-skill`, `independent-diff-review-skill`, `issue-to-tested-pr-skill`,
`release-and-docs-skill`, and `simplify-or-delete-skill`, plus their shared
`task-routing-skill` dependency. It supplies Codex agent roles and portable skills; the Copilot target is skill-only.
Use repeated `--skill` flags for an explicit selection or `--all` for the entire
collection. Select one host with `--target codex` or `--target copilot`.

For example, a documentation-only Codex project:

```bash
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/docs-project \
  --target codex --skill documentation-skill
```

The bootstrap copies regular files into the application repository:

```text
AGENTS.md                         Existing guidance plus one managed routing block
.agents/skills/<name>-skill/       Shared skill packages for both hosts
.codex/agents/*-agent.toml         Selected Codex roles
.agent-toolkit/manifest.json      Relative owned paths, hashes, and source provenance
```

Review and commit these generated files with the application so collaborators receive the
same layer after cloning. The command does not stage or commit them. Copies remain usable
when the toolkit checkout is removed or the application is relocated. Bootstrap creates
engineering guidance, not application code or a framework scaffold. It adds no dependencies,
services, credentials, global configuration, or trust settings.

The managed `AGENTS.md` block routes only to selected skills. Existing project instructions
remain intact and authoritative within system and user instructions. Work starts by
identifying the project's actual stack and commands; substantial work uses one writer and
appropriate independent review and verification. Routine tasks do not require a specialist
panel. Project Codex roles inherit the caller's model, reasoning, and permissions; the
personal installation's pinned settings remain unchanged in the toolkit source.

Codex discovers [project skill packages](https://learn.chatgpt.com/docs/build-skills) and
[project agent definitions](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Copilot can use [shared `.agents/skills` packages](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).
This toolkit ships only Codex TOML agent definitions; it does not translate them into
Copilot profiles or maintain a second role format.
Open the project in the host, complete any normal project-trust prompt, and refresh or
start a new session. File validation does not establish successful live role execution;
verify discovery and a representative task in your actual host.

Source books and private reading studies are not copied. Book-based skills can use their
original synthesized guidance, but must disclose missing local source material rather than
claim verified book evidence. Their optional personal libraries retain the paths documented
below. Scripts resolve relative to the skill actually loaded, so project copies do not
require a personal toolkit installation.

### Reproducible source checkout

For collaborators or another machine, clone the toolkit and select the exact reviewed
commit containing the bootstrap command before running it:

```bash
git clone https://github.com/RoryGlenn/agent-toolkit.git /path/to/agent-toolkit
git -C /path/to/agent-toolkit checkout --detach <full-reviewed-commit-sha>
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project --dry-run
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project
```

Replace the commit placeholder with the actual reviewed revision; a revision predating
bootstrap cannot run this command. A source archive also works. The manifest records a
source Git commit only when the checkout has its own Git root, records whether it was
dirty, and always fingerprints the exact rendered project content. An archive has a null
Git revision; a dirty checkout is not represented as an exact released commit. The manifest
contains no source, home, or application absolute paths.

### Update a project's layer

An unchanged repeat command is a no-op. Omitted skills and target reuse the existing
manifest's selection. After reviewing a newer toolkit checkout, preview and apply updates:

```bash
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project --update --dry-run
python3 /path/to/agent-toolkit/install.py bootstrap --project /path/to/my-project --update
```

Updates replace or remove only previously owned files whose content still matches the
manifest. They refuse local edits, missing managed files, and collisions with unowned files
before making changes. Keep project-specific instructions outside the marked `AGENTS.md`
block; edits there are preserved. Unrelated files, including additions within a skill's
folder, are preserved. There is no force-overwrite option. Resolve a conflict by preserving
custom work in project Git and deliberately reconciling it before retrying.

This manifest version keeps the original hosts and selected capabilities fixed. An explicit
update may add newly required shared dependencies, while preserving every previously selected
package. It still rejects unrelated skill/host reconfiguration. A deliberate
reconfiguration requires removing or reverting the prior generated layer through project
Git, including its managed instruction block and manifest, then bootstrapping the new
selection. The command does not perform that removal for you. Ordinary write failures roll
back in process; it is not a crash-atomic transaction. Review or revert updates with the
application's Git history rather than a second installation receipt system.

### Existing Copilot roles

An explicit project `bootstrap --update` retires old owned `.github/agents` files only when
their bytes still match the manifest. Locally edited roles cause refusal; unmanaged roles
remain untouched. Existing manifests selecting Copilot remain valid and become skill-only.

Personal installs do not delete existing Copilot wrappers or their source checkouts. The
skill-only target preserves those files; use the original restoration receipt or deliberately
manage a separate migration if you want to retire them. Updating the repository alone does
not update a running host session or silently remove personal configuration.

## Naming convention: skills and agents

A **skill** is reusable instructions, references, and optional tools loaded by the current
agent. An **agent** is a host-specific worker role to which a parent can delegate work.
Installing an agent definition does not start a permanent worker or service.

Every toolkit name states its type:

| Artifact | Required naming pattern | Example |
| --- | --- | --- |
| Skill directory and `SKILL.md` frontmatter `name` | `<task-or-domain>-skill` | `skills/documentation-skill/SKILL.md`, invoked as `$documentation-skill` |
| Codex agent file | `<role-or-domain>-agent.toml` | `agents/codex/documentation-agent.toml` |
| Codex agent `name` and delegation identifier | Filename stem converted to snake_case, ending `_agent` | `documentation_agent` |
| Display names | End with **Skill** or **Agent** according to the artifact | **Documentation Skill**, **Documentation Agent** |

Use lowercase kebab-case for directory and file stems. New agent definitions use Codex
TOML only. Legacy Copilot filenames remain recognized for ownership-safe cleanup, not new
agent authoring. Keep the host-defined
`SKILL.md` and optional `agents/openai.yaml` names unchanged: the latter contains skill UI
metadata and does not define a separate worker. `python3 install.py check` enforces skill
directory/frontmatter names, agent filenames and runtime names, and agent associations.

“Specialist” describes expertise in prose; it is not an artifact type or naming suffix.
A workflow skill can use shared agents or run without a dedicated agent.

For example, these Codex prompts use the same guidance in different ways:

- **Use the current agent:** “Use `$software-design-skill` to review this API.”
- **Delegate to another worker:** “Ask `software_design_agent` to review this API.”

The first loads the skill into the current agent's work. The second asks for a worker using
the named role, which loads that skill. Use the exact identifiers in the catalog below;
skill names and role names are distinct. If a host cannot dispatch a named role, follow
the skill's documented fallback rather than claiming a separate specialist ran.

## Included skills

The role columns show **roles installed with the selected skill**, not the state of your
current installation. **None** means the installer supplies the skill without a named role
for that host. `python3 install.py list` reads these associations from `install.py` and the
actual role names from their definitions.

### Book-based skills and their agents

| Skill | Use it for | Codex roles installed | Copilot roles installed |
| --- | --- | --- | --- |
| [documentation-skill](skills/documentation-skill/SKILL.md) | Documentation and reader task success, using *Docs for Developers*. | [documentation_agent](agents/codex/documentation-agent.toml) | None (skills only) |
| [ddia-skill](skills/ddia-skill/SKILL.md) | All 14 DDIA chapters through scoped engineering procedures and portable concept references. | [ddia_agent](agents/codex/ddia-agent.toml) | None (skills only) |
| [software-design-skill](skills/software-design-skill/SKILL.md) | Module boundaries, API contracts, and maintenance complexity, using *A Philosophy of Software Design*. | [software_design_agent](agents/codex/software-design-agent.toml) | None (skills only) |

### DDIA workflow skills

These discoverable entry points share `ddia-skill`; selecting any one includes the shared
package automatically in personal installations and portable project copies. Codex installs
one `ddia_agent` role, even when several workflow skills are selected. Other hosts use the
portable skills directly; the Copilot target installs no named roles. The default `ddia-skill` already contains all procedures/references;
select these optional entry points when separate workflow discovery is useful.

| Skill | Outcome |
| --- | --- |
| [ddia-assess-skill](skills/ddia-assess-skill/SKILL.md) | Decide whether a mechanism is necessary. |
| [ddia-design-skill](skills/ddia-design-skill/SKILL.md) | Compare architectures from workload and invariants. |
| [ddia-review-skill](skills/ddia-review-skill/SKILL.md) | Review consequential data changes and generated rules. |
| [ddia-validate-skill](skills/ddia-validate-skill/SKILL.md) | Construct falsifiable concurrency/failure experiments. |
| [ddia-migrate-skill](skills/ddia-migrate-skill/SKILL.md) | Plan compatible evolution, backfill and cutover. |
| [ddia-operate-skill](skills/ddia-operate-skill/SKILL.md) | Assess capacity, overload, restore and reconciliation. |
| [ddia-explain-skill](skills/ddia-explain-skill/SKILL.md) | Explain concepts through concrete decisions and examples. |

### Shared task routing

[task-routing-skill](skills/task-routing-skill/SKILL.md) is a small shared instruction package
with no named role. Every other shipped skill includes it as a dependency. A selected
specialist is a default expertise, not a requirement to force unrelated questions through
that procedure. Simple questions can load the relevant installed skill directly; consequential
bounded work can delegate to an available specialist and return to the current owner.
Mixed tasks keep one owner, explicit no-delegation requests are honored, and routed subtasks
do not bounce recursively between specialists. Trivial requests need no routing ceremony.

Named roles use only Codex TOML. Native Codex delegation returns a specialist result to
the current owner; direct skill loading and delegation do not change the visible agent
picker. Other hosts can use the portable skill guidance, but this package supplies no
Copilot agent profiles, cross-host role translation or universal UI switching.

Selected installation remains selective: installing only documentation supplies documentation
and routing guidance, not every specialist. The policy requires a disclosed, bounded fallback
when domains/tools are unavailable; install desired capabilities explicitly or use the default
engineering bootstrap. In the bounded CLI checks, one missing-skill case answered generally
without discovering/disclosing the missing capability and remains a partial result.
No global settings, model/provider defaults, permissions or account configuration are changed.
See the [routing evaluation matrix](skills/task-routing-skill/evals/README.md) and
[current routing assessment](standards/authoring/reviews/routing.md) for observed coverage and
host limitations. CLI execution does not by itself establish VS Code GUI behavior.

### Workflow and task skills

| Skill | Use it for | Codex roles installed | Copilot roles installed |
| --- | --- | --- | --- |
| [independent-diff-review-skill](skills/independent-diff-review-skill/SKILL.md) | Independent review of a branch, pull request, commit, or working-tree change. | [adversarial_reviewer_agent](agents/codex/adversarial-reviewer-agent.toml), [verifier_agent](agents/codex/verifier-agent.toml) | None |
| [issue-to-tested-pr-skill](skills/issue-to-tested-pr-skill/SKILL.md) | Implementation by one writer, followed by independent review and verification. | [implementation_owner_agent](agents/codex/implementation-owner-agent.toml), [adversarial_reviewer_agent](agents/codex/adversarial-reviewer-agent.toml), [verifier_agent](agents/codex/verifier-agent.toml) | None |
| [release-and-docs-skill](skills/release-and-docs-skill/SKILL.md) | Package, installation, upgrade, and release-documentation verification. | None | None |
| [simplify-or-delete-skill](skills/simplify-or-delete-skill/SKILL.md) | Proposals to reduce unnecessary complexity. | None | None |

The writer, reviewer, and verifier are shared engineering roles. Selecting both engineering
workflows installs their shared roles once. On hosts without named custom roles, those
workflows use separate generic agents when delegation is available and disclose when
independent evidence cannot be obtained.

## Repository map

```text
skills/<task-or-domain>-skill/
  SKILL.md                 Reusable instructions and invocation boundary
  agents/openai.yaml       Optional skill display metadata, not a named role
  references/, scripts/    Supporting material or tools, when needed
agents/
  codex/*-agent.toml       Named Codex agent definitions
books/                     Included source books; not skills or agent roles
install.py                 Catalog and CLI for personal install and project bootstrap
project_bootstrap.py        Portable project copies, ownership, and updates
tests/                     Package, retrieval, and installer behavior checks
```

Detailed personal studies and some source books live in `~/.local/share/<specialist>/`,
outside this checkout; see the specialist setup sections below. The top-level `agents/`
directory contains roles. A skill's optional `agents/openai.yaml` describes how that skill
appears in the host and does not create a separate worker.

## Personal installation

The installer requires Python 3.11 or newer on macOS or Linux. It uses the standard library
and creates links to this checkout; keep the checkout in a stable location. No service,
credentials, or runtime dependencies are needed to install it.

Run these commands from the repository root:

```bash
python3 install.py list
python3 install.py check
python3 install.py install --target codex --skill documentation-skill --dry-run
python3 install.py install --target codex --skill documentation-skill
```

Restart or refresh your agent session, then invoke `$documentation-skill` for a documentation task. The new session should show the installed skill and `documentation_agent` role. Installation checks files and links; actual model behavior also depends on the host, selected model, and available tools.

Install several skills by repeating `--skill`, or install the full collection:

```bash
python3 install.py install --target codex --all
python3 install.py install --target copilot --skill documentation-skill
```

Select skills with `--skill`; their associated roles are included automatically, as shown
in the catalog above. You do not need to install each role separately. For example,
selecting `release-and-docs-skill` installs only that workflow skill, while selecting `ddia-skill`
for Codex installs its skill and the `ddia_agent` role.

| Target | Skills | Agent definitions |
| --- | --- | --- |
| Codex | `~/.agents/skills/<name>` | `${CODEX_HOME:-~/.codex}/agents/` |
| Copilot (skills only) | `~/.copilot/skills/<name>` | None |

Codex's [skill discovery](https://learn.chatgpt.com/docs/build-skills) supports symbolically linked skill directories. Its [agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents) discovers custom TOML roles. Codex 0.165.0 opens role files without following symbolic links at runtime, so the installer creates hard links for Codex roles: regular files sharing the canonical source inode. Skills remain symbolic links. Existing Codex role symlinks require a selected reinstall with `--backup-existing`; unselected roles are untouched. The installer does not change global `AGENTS.md`, model settings, host configuration, or permissions. Imported engineering roles retain their existing model selections; edit `agents/codex/*.toml` if your account uses different models. Their `sandbox_mode` fields are retained from the original definitions, but current Codex does not use those fields to override the parent session's permissions. Review-only behavior is expressed in the role instructions.

Copilot can also discover shared `~/.agents/skills` content. Avoid separately maintaining another copy of a skill it already discovers. Host versions can differ in how duplicate names appear; inspect the skill picker after installation.

To test an installation without affecting your normal setup, supply `--home /path/to/disposable-home` outside the toolkit checkout. This ignores inherited `CODEX_HOME`; `--codex-home /explicit/path` can override the agent directory deliberately. The source checkout, active and legacy installation directories, and backup storage must be separate: aliases and nested locations are rejected before changes. The `install` subcommand handles personal links; use `bootstrap` for portable project copies. Windows installation is not supported.

## DDIA skill and agent

Install the shared suite with `python3 install.py install --target codex --skill ddia-skill`.
For a separate workflow entry point, select `--skill ddia-migrate-skill` (or another DDIA
workflow); the installer includes its required shared skill. Bootstrap has the same dependency
closure. The selection manifest records both so copied projects remain portable.

In a fresh session invoke `$ddia-skill`, a selected `$ddia-<mode>-skill`, or delegate a
consequential task to `ddia_agent`. The role inherits caller model/reasoning/permissions.
If named-role dispatch is unavailable, use the skill directly or assign a standard worker
that reads it; disclose the fallback. Consultation/review supports the existing writer;
implementation requires explicit sole ownership.

The portable package includes [topic routes](skills/ddia-skill/references/routing.md),
70 concept clusters across all 14 substantive second-edition chapters, seven procedures,
and optional data-contract/decision/handoff assets. Each cluster has applicability, an applied
procedure, qualifications, incorrect/sufficient examples, falsification and exact source
locators. The [coverage ledger](skills/ddia-skill/references/coverage.json) records authored
guidance separately from bounded experiments and measured agent behavior. The fixed number
of clusters is an organization choice, not a completeness or competence score.

Examples:

- “Use $ddia-assess-skill to decide whether this job needs durable orchestration.”
- “Ask ddia_agent to review transaction boundaries and recognize correct protections.”
- “Use $ddia-migrate-skill to plan a compatible event-schema rollout and replay.”
- “Use $ddia-skill to compare filtered vector retrieval against an exact baseline.”

Resolve helper paths relative to the skill actually loaded:

```bash
python3 /resolved/ddia-skill/scripts/guide.py route 'offline edits and conflicting writes'
python3 /resolved/ddia-skill/scripts/guide.py topics --chapter 12
python3 /resolved/ddia-skill/scripts/guide.py concept write-skew
python3 /resolved/ddia-skill/scripts/guide.py check
python3 /resolved/ddia-skill/scripts/experiments.py all
```

The [DDIA Second Edition EPUB](books/designing-data-intensive-applications-2nd-edition.epub)
is included under `books/`. Original source retrieval remains an optional personal library
at `~/.local/share/ddia-specialist/`; it is not copied by project bootstrap. Original practical
references work without it, but an agent must disclose missing original-source evidence.
From the repository root after a personal install:

```bash
python3 ~/.agents/skills/ddia-skill/scripts/book.py init --epub books/designing-data-intensive-applications-2nd-edition.epub
python3 ~/.agents/skills/ddia-skill/scripts/book.py verify
python3 ~/.agents/skills/ddia-skill/scripts/book.py search 'dedupe' --chapter 8
python3 ~/.agents/skills/ddia-skill/scripts/book.py read --ref 'OEBPS/ch08.html#sec_transactions_write_skew'
python3 ~/.agents/skills/ddia-skill/scripts/book.py neighbors --ref 'OEBPS/ch08.html#sec_transactions_write_skew'
```

The importer targets this second-edition EPUB layout and refuses conflicting/incomplete
existing state. Search ranks partial and alias matches; results and neighboring headings are
navigation, not sufficient claim evidence. Read original arguments/qualifications before
attribution. Reads print explicit continuation offsets. Inspect original figures/tables when
layout affects interpretation; text extraction does not interpret images. Source integrity
and resolving anchors do not by themselves establish semantic fidelity or comprehension.

Project bootstrap routes consequential design and data changes to relevant procedures,
without imposing a specialist panel on unrelated edits or global mandatory architecture gates.
Use existing project documentation to record agreed invariants and handoffs. Executable tests,
not Markdown authority, enforce explicitly agreed requirements.

[DDIA evaluation instructions](skills/ddia-skill/evals/README.md) provide seventeen public
constructed reasoning cases, eight bounded counterexample experiments and a three-arm
baseline/current/redesigned comparison planner with frozen resources, repeated trials and
independent semantic scoring. It does not launch models or enforce isolation/budgets. Real
SQLite experiments and deterministic models are labeled separately from live distributed
systems. Authored coverage and fixture success do not establish production correctness or
specialist superiority. The earlier local four-task comparison tied both arms at 32/32 and
showed traceability, not a correctness improvement; personal evidence remains in
`~/.local/share/ddia-specialist/evaluation/`.

## Software design skill and agent

Install with `python3 install.py install --target codex --skill software-design-skill`.
In a fresh session, invoke `$software-design-skill`, or ask the parent to delegate to
`software_design_agent`. The role inherits the caller's model and reasoning settings.
Consultation and review are read-only; implementation requires explicit sole ownership.
Hosts without named-role dispatch can use the skill directly or a standard agent instructed
to read it first. That fallback does not establish successful named-role loading.

The specialist applies John K. Ousterhout's *A Philosophy of Software Design*, Second Edition,
to concrete caller and maintenance costs. It compares consequential alternatives, checks
which knowledge a boundary hides, and preserves required contracts. It does not mechanically
enforce small functions, large modules, comment quotas, or blanket bans on familiar patterns.
Its relevance-based description adds no mandatory consultation to routine changes.

Examples:

- “Use $software-design-skill to compare the module boundaries for this feature.”
- “Ask software_design_agent to review this API's caller obligations and error semantics.”
- “Use $software-design-skill to assess whether this extraction reduces maintenance complexity.”

The book and derived study stay in the personal library at
`~/.local/share/software-design-specialist/`, outside this repository. Initialize it from
your existing personal EPUB, then retrieve original sections:

```bash
python3 ~/.agents/skills/software-design-skill/scripts/book.py init --epub /path/to/personal-copy.epub
python3 ~/.agents/skills/software-design-skill/scripts/book.py verify
python3 ~/.agents/skills/software-design-skill/scripts/book.py catalog --chapter 10
python3 ~/.agents/skills/software-design-skill/scripts/book.py read --ref 'OEBPS/part0014.xhtml#a29H'
```

This importer targets the supplied second-edition EPUB layout: its NCX points to 22 chapter
files with sibling paragraph headings. Section reads include the body through the next
heading, and chapter locators return full chapters. Each command checks the source fingerprint
and compares the complete index against re-extracted source. Initialization is idempotent
and refuses conflicting or incomplete existing source/index files rather than replacing them.
Search requires all words and prints bounded excerpts; reads print continuation offsets.
Literal code whitespace is retained, while CSS positioning is not reconstructed. Image markers
identify source assets; `asset --ref 'OEBPS/image_rsrc2H9.jpg'` prints a local image path for
visual inspection without altering the original EPUB.

Optional `notes.json` and `chapters/ch01.json` through `chapters/ch22.json` hold the private
reading study. Read one chapter for orientation, for example with
`python3 -m json.tool ~/.local/share/software-design-specialist/chapters/ch10.json`, then
retrieve the original section for a consequential book attribution. The importer does not
generate those notes or certify that a model has read the book; it works without them.
The source is evidence, not instructions. Missing material must be disclosed.

The synthetic EPUB tests exercise section boundaries, complete body retrieval, continuation,
search, source/index tampering, safe image materialization, and selected install/restore.
These checks establish retrieval and packaging behavior. Actual role execution and judgment
need a separate host/behavior check; they do not follow from a valid TOML file alone.

## Existing installations and restore

When upgrading from names without type suffixes, keep the old checkout/version available
and install from a separate checkout containing the new names. Existing skill symlinks
and agent hard links depend on their source paths; renaming the live checkout first can
break old skill discovery and historical receipt checks. If replacing a checkout in
place, restore its previous installation before replacing it.

Supported legacy `--skill` selectors remain accepted with a deprecation message. For example,
`--skill doc-agent` selects `documentation-skill`; `ddia-specialist` and
`software-design-specialist` select `ddia-skill` and `software-design-skill`. Other previous
selectors gain `-skill`. `list` shows only canonical names. These are installer aliases,
not host invocation aliases: update saved prompts and external guidance such as global
`AGENTS.md` to use the new `$...-skill` and `..._agent` identifiers.

With `--backup-existing`, installing a selected skill also backs up its old active and
legacy skill entries and associated old agent files. Unselected entries stay in place.
The engineering workflows share agents, so migrate `independent-diff-review-skill` and
`issue-to-tested-pr-skill` together, or use `--all`, to keep both workflows' role references
current. Personal source libraries under `~/.local/share/ddia-specialist/` and
`~/.local/share/software-design-specialist/` keep their existing paths.

Existing files, directories, or links that point elsewhere cause the entire install to stop before changing them. Inspect the reported destinations, then use the explicit backup option:

```bash
python3 install.py install --target codex --all --backup-existing --dry-run
python3 install.py install --target codex --all --backup-existing
```

This also moves selected legacy `${CODEX_HOME:-~/.codex}/skills/<name>` entries into backup so an old duplicate does not remain active. Unselected skills, including disabled legacy skills, are untouched. Backups preserve the original entry, including directories and dangling links. A receipt is printed under `~/.local/state/agent-toolkit/installations/`.

Keep that receipt and its numbered backup entries together. Retain the old source checkout
for restored symlinks and any historical hard-link receipts to remain usable. Restore an installation with the exact path printed by the installer:

```bash
python3 install.py restore /path/to/receipt.json --dry-run
python3 install.py restore /path/to/receipt.json
```

Restore first checks every managed destination. It also refuses to remove a shared skill
or role still required by a surviving managed skill linked to the same source checkout; restore the dependent installation
first. A recorded backup is restored as the prior entry, without claiming compatibility
of that historical version with newer consumers. It refuses to overwrite a link or file you replaced after installation. It removes the toolkit links, restores prior entries, and keeps the receipt as a record. Empty host directories remain. Ordinary installation or restoration errors trigger rollback; interrupted processes and manual changes to receipts require inspection before further changes. Backups use filesystem moves, so a custom Codex home on another filesystem may prevent a migration; a failed move is rolled back.

## Maintain the collection

Use the [shared agent and skill authoring standard](standards/authoring/README.md) for
current and future packages. It includes reusable skill and host-role templates, a primary
research ledger, a review worksheet, and an adoption inventory covering all shipped skills
and roles. It is community-aligned and proposed; no external endorsement or universal
performance improvement is claimed. The authoring check validates structure and evidence
locations, while behavioral confidence requires inspecting actual task results.

The [standalone authoring package](skill_authoring/README.md) uses the open Agent Skills
format, OpenAI's actual Codex initializer, and Anthropic's paired evaluation/reporting
workflow with a Codex adapter. Upstream revisions, licenses, and exact source hashes are
included. This package does not load or reuse the toolkit's custom skills, roles, or benchmarks.

Edit `skills/<name>/` and `agents/<host>/` here. Skill symlinks expose source changes immediately. Codex role hard links share in-place edits, but an editor/Git operation that replaces a source file atomically leaves the installed role on the old inode. Re-run the selected installation to check it; if it reports a conflict, use `--backup-existing` to preserve the old role before refreshing it. Restoration also refuses a role whose canonical source inode changed. Start a fresh host session when it caches instructions. Re-run the installer after adding a skill or moving the checkout. It is safe to repeat an unchanged installation.

Codex role hard links require the toolkit and Codex agent directory to be on the same filesystem. Cross-volume installation fails explicitly and rolls back; place the checkout and Codex home on the same volume. The installer does not silently fall back to a role symlink that the runtime cannot load.

Keep a skill's methods, supporting references, examples, and useful validation cases together. Store project facts in that project's existing guidance. Preserve source attribution and the distinction between observed behavior, fixture checks, model evaluations, and real user outcomes.

For every new, modified, or imported skill or agent, follow the
[naming convention](#naming-convention-skills-and-agents). Create a skill at
`skills/<task-or-domain>-skill/SKILL.md` with a frontmatter `name` matching its directory
and a `description`.
Add scripts, references, or assets only when useful. An optional custom agent lives in
`agents/<host>/` with the required agent filename and identifier; add its skill association
to `AGENTS` in `install.py`. Run the [development checks](#development-checks) and relevant
behavior checks before installing the change.

See the [completed authoring adoption assessment](standards/authoring/reviews/README.md)
for per-artifact dispositions, representative cases and remaining host/behavior checks.
Reviewed artifacts retain their useful structures; the standard does not require identical
headings or turn structural validation into a quality certification.

## Development checks

`uv` manages the development tools; it is not required for installation.

```bash
uv sync --group dev
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python authoring.py check
python3 install.py check
git diff --check
```

The tests cover personal installs and restore, project copies and relocation, selected host layouts, ownership conflicts, explicit updates, dry runs, rollback, source provenance, source validation, custom homes, and the docs environment checker. The docs skill also contains [behavior evaluation cases](skills/documentation-skill/evals/README.md) and [optional site tooling](skills/documentation-skill/tooling/README.md). Those tools have their own prerequisites; passing the installer tests does not establish live host loading, browser accessibility, or documentation quality.

After installing the optional Node tools and Chromium as described in the tooling guide,
run `python3 tests/browser_regression.py` from this repository root. This separate suite
checks the shipped documentation site check against loopback-only readiness and
accessibility fixtures; it is excluded from ordinary unit-test discovery.
The separate documentation browser workflow runs it for pull requests that change the
runner or site tooling, for matching changes on `main`, and on manual dispatch.

## Development benchmark

The [public development benchmark](benchmarks/README.md) supplies twelve original RecordBatch
cases for the three specialists and their integrated workflow. It includes executable objective
oracles, reference/wrong controls, isolated Codex CLI runs, three comparison arms, and paired
reports that retain failures and unresolved human review. Difficulty is provisional; no live
performance improvement is claimed by its deterministic checks.

```bash
uv run python -m benchmarks list
uv run python -m benchmarks validate
```

See the benchmark guide before a model run: explicit source profiles, signed-in CLI credential
selection, native isolation canaries and bounded budgets are required. CI runs only trusted
repository controls and the existing checks, with no model credentials or paid calls.

## Sources and ownership

This toolkit is the maintained source for the collected skills and agent definitions. Original repositories and installations are retained until deliberately migrated; no source repository, published history, or old installer manifest is changed by this package.

- The docs package, historical Copilot wrapper, and optional browser regression runner came from [RoryGlenn/doc-agent](https://github.com/RoryGlenn/doc-agent), commit `589d26d92d9ff29658e88af795e5164972329e00`. The current package retains the skill and Codex role; the former Copilot wrapper is removed. The fuller repository package incorporates the earlier installed Codex skill and adds tools, templates, and evaluations. Its [book foundation](skills/documentation-skill/references/book-foundation.md) credits the authors and explains the original synthesis. The [archived standalone validation record](docs/validation/doc-agent-2026-09-26.md) preserves the initial package's evidence and limits; it does not validate this toolkit or later changes. The source [Docs for Developers, Second Edition EPUB](books/docs-for-developers-2nd-edition.epub) is included for reference; the agent does not require it at runtime. Its original copyright notices remain in the EPUB; inclusion does not assign the book a new license.
- *Designing Data-Intensive Applications*, Second Edition, by Martin Kleppmann and Chris Riccomini (O'Reilly Media, 2026), is included as the DDIA specialist's source. Its original copyright notices remain in the EPUB; inclusion does not assign the book a new license.
- The software-design specialist uses an original synthesis of *A Philosophy of Software Design*, Second Edition, by John K. Ousterhout (Yaknyam Press, 2021). Its personal EPUB and detailed reading notes are kept outside this repository; the skill retrieves them locally and does not redistribute the source.
- Four engineering skills and three Codex roles came from the `RoryGlenn/RoryGlenn` profile repository. Their previous installation also managed global guidance, configuration, and `codex-lanes`; those remain outside this toolkit. The workflow can use native Git worktrees when that helper is unavailable.
- The Codex docs wrapper came from Rory's local custom configuration.
- The disabled `hatch-pet` installation is excluded because its provenance and overlap with the installed Work Pets plugin need separate resolution. Bundled and third-party plugin skills are not copied.

This repository has no redistribution license assigned. Review provenance and choose licensing before publishing it for others.
