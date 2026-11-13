# Proposal

## Why

Agent Toolkit has software-design judgment and independent implementation/review roles, but no specialist procedure for changing existing code whose behavior is poorly protected by tests. A specialist grounded in Michael C. Feathers' *Working Effectively with Legacy Code* can help establish observable behavior, isolate obstructive dependencies, and sequence a bounded change without losing existing contracts.

## What Changes

- Add `legacy-code-skill`, displayed as **Legacy Code Skill**, and a thin Codex `legacy_code_agent` role in `agents/codex/legacy-code-agent.toml`, displayed as **Legacy Code Agent**. Inherit the caller's model, reasoning settings, tools, and permissions.
- Study all 25 chapters, the refactoring appendix, and relevant front/back matter. Connect each chapter and all 24 dependency-breaking techniques to practical decisions, exact source locators, qualifications, and evaluation coverage. Record unread or inaccessible material explicitly; an index is not evidence of study.
- Provide local-only EPUB initialization, integrity verification, chapter/section retrieval, literal search, and safe figure access. Keep the original book, extracted text, private reading notes, and raw evaluation runs outside Git and installed public packages.
- Teach characterization of actual behavior, change-impact analysis, seams and their enabling points, minimal dependency breaking, and incremental change/verification. Separate observed behavior, intended requirements, authorized bug fixes, and unverified assumptions.
- Integrate selective personal/project installation, the shared task-routing policy, metadata, documentation, and the authoring adoption inventory. Keep the existing default project skill selection unchanged; explicit selection and `--all` can include the new capability.
- Add original synthetic retrieval/install fixtures and realistic behavior cases. Record discovery, direct skill use, named-role execution, source access, and comparative value as separate evidence categories.

## Capabilities

### New Capabilities

- `legacy-code-guidance`: Evidence-grounded safe-change advice, source-study coverage, useful handoffs, and ownership boundaries for poorly tested existing code.
- `legacy-code-source-library`: Private, offline initialization and verifiable retrieval from the supported Feathers EPUB.
- `legacy-code-toolkit-integration`: Naming, selective installation, shared routing, host integration, documentation, and honest assessment of the new package.

### Modified Capabilities

None. `openspec list --specs` reports no existing capability specifications. Existing installation and routing code will be extended within the new capability contracts, without retroactively specifying unrelated toolkit behavior.

## Impact

Expected implementation touches `skills/legacy-code-skill/`, `agents/codex/legacy-code-agent.toml`, `install.py`, `project_bootstrap.py`, shared routing guidance/cases, `README.md`, `pyproject.toml`, relevant tests, and authoring inventory/review records. Reassess changed reviewed entrypoints and their supporting resources before refreshing fingerprints; preserve historical evidence.

No new runtime service, cloud dependency, API key, Copilot role format, or automatic migration is proposed. No production repository refactoring is included. The initial request authorized planning; implementation was subsequently requested, followed by the established issue-to-merge trigger. GitHub delivery is tracked in [issue #22](https://github.com/RoryGlenn/agent-toolkit/issues/22). Personal installation and quota-consuming model evaluations remain separate actions. Current implementation evidence and remaining gaps are in [progress.md](progress.md).
