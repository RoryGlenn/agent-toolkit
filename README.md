# Agent Toolkit

Rory's reusable agents and skills, maintained in one repository. Install the skills you need for a project, then improve their shared instructions as you use them. Projects still supply their own architecture, audience, commands, terminology, and conventions.

The installer requires Python 3.11 or newer on macOS or Linux. It uses the standard library and creates links to this checkout; keep the checkout in a stable location. No service, credentials, or runtime dependencies are needed to install it.

## Included skills

| Skill | Use it for |
| --- | --- |
| [doc-agent](skills/doc-agent/SKILL.md) | Documentation grounded in *Docs for Developers*: writing, review, maintenance, examples, and reader task success. |
| [ddia-specialist](skills/ddia-specialist/SKILL.md) | Data architecture, transaction/concurrency correctness, replication, messaging, and recovery grounded in a personal DDIA Second Edition EPUB. |
| [independent-diff-review](skills/independent-diff-review/SKILL.md) | Independent review of a branch, pull request, commit, or working-tree change. |
| [issue-to-tested-pr](skills/issue-to-tested-pr/SKILL.md) | One-writer implementation followed by independent review and verification. |
| [release-and-docs](skills/release-and-docs/SKILL.md) | Package, installation, upgrade, and release-documentation verification. |
| [simplify-or-delete](skills/simplify-or-delete/SKILL.md) | Evidence-based proposals to reduce unnecessary complexity. |
| [career-positioning](skills/career-positioning/SKILL.md) | Evidence-backed profile, resume, and portfolio improvements; includes Rory's positioning preferences. |
| [recruiter-followup](skills/recruiter-followup/SKILL.md) | Recruiter triage, response audits, and requested replies. |

Codex has five agent definitions: `doc_agent`, `ddia_specialist`, `implementation_owner`, `adversarial_reviewer`, and `verifier`. Copilot has the existing Doc Agent definition. Skills carry reusable procedures; agent definitions configure the specialist that uses them.

## Install

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

Selecting `doc-agent` also installs its host's agent definition. Selecting `ddia-specialist` installs the `ddia_specialist` Codex role. For Codex, `independent-diff-review` installs the reviewer and verifier roles; `issue-to-tested-pr` installs those roles plus the implementation owner. Shared roles are installed once when selecting both skills. The remaining skills need no separate agent definition. On hosts without named custom roles, the review workflows use separate generic agents when delegation is available and disclose when independent evidence cannot be obtained.

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

- The docs package and Copilot wrapper came from [RoryGlenn/doc-agent](https://github.com/RoryGlenn/doc-agent), commit `589d26d92d9ff29658e88af795e5164972329e00`. The fuller repository package incorporates the earlier installed Codex skill and adds tools, templates, and evaluations. Its [book foundation](skills/doc-agent/references/book-foundation.md) credits the authors and explains the original synthesis. The book itself is not included.
- *Designing Data-Intensive Applications*, Second Edition, by Martin Kleppmann and Chris Riccomini (O'Reilly Media, 2026), is included as the DDIA specialist's source. Its original copyright notices remain in the EPUB; inclusion does not assign the book a new license.
- Four engineering skills and three Codex roles came from the `RoryGlenn/RoryGlenn` profile repository. Their previous installation also managed global guidance, configuration, and `codex-lanes`; those remain outside this toolkit. The workflow can use native Git worktrees when that helper is unavailable.
- The Codex docs wrapper, `career-positioning`, and `recruiter-followup` came from Rory's local custom configuration. Personal preferences are intentional; other users should adapt them.
- The disabled `hatch-pet` installation is excluded because its provenance and overlap with the installed Work Pets plugin need separate resolution. Bundled and third-party plugin skills are not copied.

This repository has no redistribution license assigned. Review provenance and choose licensing before publishing it for others.
