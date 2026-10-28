# Agent Toolkit

Rory's reusable skills and named agent roles, maintained in one repository. Choose a skill
for the work you want to do; the installer also supplies any roles associated with that
skill. Projects still supply their own architecture, audience, commands, terminology,
and conventions.

## Skills, roles, and specialists

| Term | Meaning in this project |
| --- | --- |
| **Skill** | Reusable instructions, references, and optional tools that the current agent can load. Its entrypoint is `skills/<name>/SKILL.md`. |
| **Named agent role** | A host-specific definition of an agent's job. In Codex, a parent can delegate to a separate worker with that role. Role files live in `agents/<host>/`; installing one does not start a permanent worker or service. |
| **Specialist** | A description of expertise, not a third file type. The three book-based specialists below each combine a skill with a dedicated Codex role. |
| **Workflow skill** | A skill that coordinates a process. It may use shared engineering roles; it does not necessarily have a dedicated agent. |

For example, these Codex prompts use the same guidance in different ways:

- **Use the current agent:** “Use `$software-design-specialist` to review this API.”
- **Delegate to another worker:** “Ask `software_design_specialist` to review this API.”

The first loads the skill into the current agent's work. The second asks for a worker using
the named role, which loads that skill. Use the exact identifiers in the catalog below;
skill names and role names are distinct. If a host cannot dispatch a named role, follow
the skill's documented fallback rather than claiming a separate specialist ran.

## Included skills

The role columns show **roles installed with the selected skill**, not the state of your
current installation. **None** means the installer supplies the skill without a named role
for that host. `python3 install.py list` reads these associations from `install.py` and the
actual role names from their definitions.

### Book-based specialists

| Skill | Use it for | Codex roles installed | Copilot roles installed |
| --- | --- | --- | --- |
| [doc-agent](skills/doc-agent/SKILL.md) | Documentation and reader task success, using *Docs for Developers*. | [doc_agent](agents/codex/doc-agent.toml) | [Doc Agent](agents/copilot/doc-agent.agent.md) |
| [ddia-specialist](skills/ddia-specialist/SKILL.md) | Data architecture, transactions, replication, and recovery, using DDIA Second Edition. | [ddia_specialist](agents/codex/ddia-specialist.toml) | None |
| [software-design-specialist](skills/software-design-specialist/SKILL.md) | Module boundaries, API contracts, and maintenance complexity, using *A Philosophy of Software Design*. | [software_design_specialist](agents/codex/software-design-specialist.toml) | None |

### Workflow and task skills

| Skill | Use it for | Codex roles installed | Copilot roles installed |
| --- | --- | --- | --- |
| [book-to-agent](skills/book-to-agent/SKILL.md) | Study a book and build a grounded specialist skill or agent. The workflow itself has no factory role. | None | None |
| [independent-diff-review](skills/independent-diff-review/SKILL.md) | Independent review of a branch, pull request, commit, or working-tree change. | [adversarial_reviewer](agents/codex/adversarial-reviewer.toml), [verifier](agents/codex/verifier.toml) | None |
| [issue-to-tested-pr](skills/issue-to-tested-pr/SKILL.md) | Implementation by one writer, followed by independent review and verification. | [implementation_owner](agents/codex/implementation-owner.toml), [adversarial_reviewer](agents/codex/adversarial-reviewer.toml), [verifier](agents/codex/verifier.toml) | None |
| [release-and-docs](skills/release-and-docs/SKILL.md) | Package, installation, upgrade, and release-documentation verification. | None | None |
| [simplify-or-delete](skills/simplify-or-delete/SKILL.md) | Proposals to reduce unnecessary complexity. | None | None |
| [recruiter-followup](skills/recruiter-followup/SKILL.md) | Recruiter triage, response audits, and requested replies. | None | None |

The writer, reviewer, and verifier are shared engineering roles. Selecting both engineering
workflows installs their shared roles once. On hosts without named custom roles, those
workflows use separate generic agents when delegation is available and disclose when
independent evidence cannot be obtained.

## Repository map

```text
skills/<skill-name>/
  SKILL.md                 Reusable instructions and invocation boundary
  agents/openai.yaml       Optional skill display metadata, not a named role
  references/, scripts/    Supporting material or tools, when needed
agents/
  codex/*.toml             Named Codex role definitions
  copilot/*.agent.md       Named Copilot agent definitions
books/                     Included source books; not skills or agent roles
install.py                 Skill discovery, role associations, installation, restore
tests/                     Package, retrieval, and installer behavior checks
```

Detailed personal studies and some source books live in `~/.local/share/<specialist>/`,
outside this checkout; see the specialist setup sections below. The top-level `agents/`
directory contains roles. A skill's optional `agents/openai.yaml` describes how that skill
appears in the host and does not create a separate worker.

## Install

The installer requires Python 3.11 or newer on macOS or Linux. It uses the standard library
and creates links to this checkout; keep the checkout in a stable location. No service,
credentials, or runtime dependencies are needed to install it.

Run these commands from the repository root:

```bash
python3 install.py list
python3 install.py check
python3 install.py install --target codex --skill doc-agent --dry-run
python3 install.py install --target codex --skill doc-agent
```

Restart or refresh your agent session, then invoke `$doc-agent` for a documentation task. The new session should show the installed skill and `doc_agent` role. Installation checks files and links; actual model behavior also depends on the host, selected model, and available tools.

Install several skills by repeating `--skill`, or install the full collection:

```bash
python3 install.py install --target codex --all
python3 install.py install --target copilot --skill doc-agent
```

Select skills with `--skill`; their associated roles are included automatically, as shown
in the catalog above. You do not need to install each role separately. For example,
selecting `book-to-agent` installs only that workflow skill, while selecting `ddia-specialist`
for Codex installs its skill and the `ddia_specialist` role.

| Target | Skills | Agent definitions |
| --- | --- | --- |
| Codex | `~/.agents/skills/<name>` | `${CODEX_HOME:-~/.codex}/agents/` |
| Copilot | `~/.copilot/skills/<name>` | `~/.copilot/agents/` |

Codex's [skill discovery](https://learn.chatgpt.com/docs/build-skills) supports symbolically linked skill directories. Its [agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents) discovers custom TOML roles. Codex 0.165.0 opens role files without following symbolic links at runtime, so the installer creates hard links for Codex roles: regular files sharing the canonical source inode. Skills and Copilot wrappers remain symbolic links. Existing Codex role symlinks require a selected reinstall with `--backup-existing`; unselected roles are untouched. The installer does not change global `AGENTS.md`, model settings, host configuration, or permissions. Imported engineering roles retain their existing model selections; edit `agents/codex/*.toml` if your account uses different models. Their `sandbox_mode` fields are retained from the original definitions, but current Codex does not use those fields to override the parent session's permissions. Review-only behavior is expressed in the role instructions.

Copilot can also discover shared `~/.agents/skills` content. Avoid separately maintaining another copy of a skill it already discovers. Host versions can differ in how duplicate names appear; inspect the skill picker after installation.

To test an installation without affecting your normal setup, supply `--home /path/to/disposable-home` outside the toolkit checkout. This ignores inherited `CODEX_HOME`; `--codex-home /explicit/path` can override the agent directory deliberately. The source checkout, active and legacy installation directories, and backup storage must be separate: aliases and nested locations are rejected before changes. The installer currently handles personal installations, not per-project copies or Windows links.

## DDIA specialist

Install with `python3 install.py install --target codex --skill ddia-specialist`.
In a fresh session, invoke `$ddia-specialist`, or ask the parent to delegate to
`ddia_specialist`. If a host/session cannot dispatch custom roles, use the skill directly
or ask a standard agent to read `~/.agents/skills/ddia-specialist/SKILL.md` before its task. The role inherits the calling model and reasoning settings.
Consultation and review return advice to the existing writer; implementation requires
explicit sole ownership. Its description enables relevance-based selection without
changing global `AGENTS.md` or adding a mandatory review step to every task.

Examples:

- “Use $ddia-specialist to assess the simplest sufficient data design for this service.”
- “Ask ddia_specialist to review the transaction boundaries in this diff for reachable races.”
- “Use $ddia-specialist to trace commit, retry, acknowledgment, and replay behavior in this consumer.”

The [DDIA Second Edition EPUB](books/designing-data-intensive-applications-2nd-edition.epub)
is included under `books/`. The extracted index, chapter syntheses, and validation evidence
remain in the personal reference library at `~/.local/share/ddia-specialist/`.
To initialize source retrieval from the repository root:

```bash
python3 ~/.agents/skills/ddia-specialist/scripts/book.py init --epub books/designing-data-intensive-applications-2nd-edition.epub
python3 ~/.agents/skills/ddia-specialist/scripts/book.py verify
python3 ~/.agents/skills/ddia-specialist/scripts/book.py search 'write skew' --chapter 8
python3 ~/.agents/skills/ddia-specialist/scripts/book.py read --ref 'OEBPS/ch08.html#sec_transactions_write_skew'
```

The importer targets this second-edition EPUB layout and refuses a different or incomplete
existing index. Initialization creates a stable local source copy and index; it does not
create chapter syntheses or claim that a model read the book. The personal `notes.md`,
`chapters/`, and `coverage.json` record the substantive reading done for this installation.
If those notes are absent, retrieve original sections directly. Search uses all query words;
shorten or vary terms when no result matches. Section reads print continuation offsets.
Text extraction preserves code whitespace and explicit exponent/subscript markers; inspect
original diagram assets when their visual content affects a decision.

Personal validation evidence is at `~/.local/share/ddia-specialist/evaluation/`.
Unit tests validate retrieval/integrity and reversible installation. The separate behavioral
comparison uses simulated project tasks and executable SQLite fixtures; it does not establish
improvement across production projects. Derived references and personal evaluation artifacts
are not included in this repository.

## Software-design specialist

Install with `python3 install.py install --target codex --skill software-design-specialist`.
In a fresh session, invoke `$software-design-specialist`, or ask the parent to delegate to
`software_design_specialist`. The role inherits the caller's model and reasoning settings.
Consultation and review are read-only; implementation requires explicit sole ownership.
Hosts without named-role dispatch can use the skill directly or a standard agent instructed
to read it first. That fallback does not establish successful named-role loading.

The specialist applies John K. Ousterhout's *A Philosophy of Software Design*, Second Edition,
to concrete caller and maintenance costs. It compares consequential alternatives, checks
which knowledge a boundary hides, and preserves required contracts. It does not mechanically
enforce small functions, large modules, comment quotas, or blanket bans on familiar patterns.
Its relevance-based description adds no mandatory consultation to routine changes.

Examples:

- “Use $software-design-specialist to compare the module boundaries for this feature.”
- “Ask software_design_specialist to review this API's caller obligations and error semantics.”
- “Use $software-design-specialist to assess whether this extraction reduces maintenance complexity.”

The book and derived study stay in the personal library at
`~/.local/share/software-design-specialist/`, outside this repository. Initialize it from
your existing personal EPUB, then retrieve original sections:

```bash
python3 ~/.agents/skills/software-design-specialist/scripts/book.py init --epub /path/to/personal-copy.epub
python3 ~/.agents/skills/software-design-specialist/scripts/book.py verify
python3 ~/.agents/skills/software-design-specialist/scripts/book.py catalog --chapter 10
python3 ~/.agents/skills/software-design-specialist/scripts/book.py read --ref 'OEBPS/part0014.xhtml#a29H'
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

## Book-to-agent workflow

Install with `python3 install.py install --target codex --skill book-to-agent`, then use:

> Use $book-to-agent with `/path/to/book.epub` to create a specialist for [the work you want it to do], following my existing agent setup.

This is a coordinating skill; it installs no additional named agent. It reuses the existing
creator, reader, installer, and engineering workflows. It guides source identification and
full agreed-scope reading, synthesis of principles and qualifications, a compact operational
skill, an optional specialist role, and independent behavioral checks. The source format is
inspected before choosing retrieval tools; books with different layouts need not share a parser.

The workflow distinguishes extraction from substantive reading, useful advice from successful
file creation, and host discovery from actual role execution. Original books and detailed
personal studies stay outside the shared package by default. It preserves existing agents
and settings and does not authorize publication or additional permissions.

## Existing installations and restore

Existing files, directories, or links that point elsewhere cause the entire install to stop before changing them. Inspect the reported destinations, then use the explicit backup option:

```bash
python3 install.py install --target codex --all --backup-existing --dry-run
python3 install.py install --target codex --all --backup-existing
```

This also moves selected legacy `${CODEX_HOME:-~/.codex}/skills/<name>` entries into backup so an old duplicate does not remain active. Unselected skills, including disabled legacy skills, are untouched. Backups preserve the original entry, including directories and dangling links. A receipt is printed under `~/.local/state/agent-toolkit/installations/`.

Keep that receipt and its numbered backup entries together. Restore an installation with the exact path printed by the installer:

```bash
python3 install.py restore /path/to/receipt.json --dry-run
python3 install.py restore /path/to/receipt.json
```

Restore first checks every managed destination. It refuses to overwrite a link or file you replaced after installation. It removes the toolkit links, restores prior entries, and keeps the receipt as a record. Empty host directories remain. Ordinary installation or restoration errors trigger rollback; interrupted processes and manual changes to receipts require inspection before further changes. Backups use filesystem moves, so a custom Codex home on another filesystem may prevent a migration; a failed move is rolled back.

## Maintain the collection

Edit `skills/<name>/` and `agents/<host>/` here. Skill symlinks expose source changes immediately. Codex role hard links share in-place edits, but an editor/Git operation that replaces a source file atomically leaves the installed role on the old inode. Re-run the selected installation to check it; if it reports a conflict, use `--backup-existing` to preserve the old role before refreshing it. Restoration also refuses a role whose canonical source inode changed. Start a fresh host session when it caches instructions. Re-run the installer after adding a skill or moving the checkout. It is safe to repeat an unchanged installation.

Codex role hard links require the toolkit and Codex agent directory to be on the same filesystem. Cross-volume installation fails explicitly and rolls back; place the checkout and Codex home on the same volume. The installer does not silently fall back to a role symlink that the runtime cannot load.

Keep a skill's methods, supporting references, examples, and useful validation cases together. Store project facts in that project's existing guidance. Preserve source attribution and the distinction between observed behavior, fixture checks, model evaluations, and real user outcomes.

For a new skill, add `skills/<name>/SKILL.md` with `name` and `description` frontmatter. Add scripts, references, or assets only when useful. An optional custom agent lives in `agents/<host>/`; add its skill association to `AGENTS` in `install.py`. Run the package and behavior checks before installing the change.

## Development checks

`uv` manages the development tools; it is not required for installation.

```bash
uv sync --group dev
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check .
uv run mypy
python3 install.py check
git diff --check
```

The tests cover selected and full installs, both host layouts, conflicts, dry runs, legacy migration, backup/restore, failure rollback, source validation, custom homes, and the docs environment checker. The docs skill also contains [behavior evaluation cases](skills/doc-agent/evals/README.md) and [optional site tooling](skills/doc-agent/tooling/README.md). Those tools have their own prerequisites; passing the installer tests does not establish live host loading, browser accessibility, or documentation quality.

## Sources and ownership

This toolkit is the maintained source for the collected skills and agent definitions. Original repositories and installations are retained until deliberately migrated; no source repository, published history, or old installer manifest is changed by this package.

- The docs package and Copilot wrapper came from [RoryGlenn/doc-agent](https://github.com/RoryGlenn/doc-agent), commit `589d26d92d9ff29658e88af795e5164972329e00`. The fuller repository package incorporates the earlier installed Codex skill and adds tools, templates, and evaluations. Its [book foundation](skills/doc-agent/references/book-foundation.md) credits the authors and explains the original synthesis. The source [Docs for Developers, Second Edition EPUB](books/docs-for-developers-2nd-edition.epub) is included for reference; the agent does not require it at runtime. Its original copyright notices remain in the EPUB; inclusion does not assign the book a new license.
- *Designing Data-Intensive Applications*, Second Edition, by Martin Kleppmann and Chris Riccomini (O'Reilly Media, 2026), is included as the DDIA specialist's source. Its original copyright notices remain in the EPUB; inclusion does not assign the book a new license.
- The software-design specialist uses an original synthesis of *A Philosophy of Software Design*, Second Edition, by John K. Ousterhout (Yaknyam Press, 2021). Its personal EPUB and detailed reading notes are kept outside this repository; the skill retrieves them locally and does not redistribute the source.
- Four engineering skills and three Codex roles came from the `RoryGlenn/RoryGlenn` profile repository. Their previous installation also managed global guidance, configuration, and `codex-lanes`; those remain outside this toolkit. The workflow can use native Git worktrees when that helper is unavailable.
- The Codex docs wrapper and `recruiter-followup` came from Rory's local custom configuration.
- The disabled `hatch-pet` installation is excluded because its provenance and overlap with the installed Work Pets plugin need separate resolution. Bundled and third-party plugin skills are not copied.

This repository has no redistribution license assigned. Review provenance and choose licensing before publishing it for others.
