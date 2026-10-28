# Tool and environment routing

## Discover before adding

Use the active host's workspace read/search/edit tools and terminal. In VS Code Copilot these capabilities are provided through the `read`, `search`, `edit`, and `execute` tool sets; `web` and `browser` help with sources and previews when enabled. Use the actual available tools, not a Codex-specific API name.

Inspect existing project instructions, style rules, supported versions, package manifests, lockfiles, and documentation build/test commands. For a useful inventory, run:

```sh
python3 /path/to/doc-agent/scripts/check_environment.py --project /path/to/project
```

The path above means this installed skill's directory, not a literal required location. Use `--json` for structured output. The checker reads bounded configuration files and looks up executable paths. It does not execute discovered binaries, repository scripts, install tools, access the network, or read environment variable values. The reported Python version is the running interpreter; other versions must be checked separately with appropriate trusted commands.

Missing optional tools are not a failed documentation task. Continue useful content work and describe any check that cannot run. Prefer an existing project's environment and lockfile over a global replacement. Use the terminal shell appropriate to macOS, Linux, or Windows.

## Match tools to the deliverable

| Deliverable | Route |
| --- | --- |
| Repository Markdown/MDX | Existing editor, source search, project style/build checks, and the actual site renderer when applicable |
| Documentation website | Existing project build and preview command; inspect rendered navigation, examples, links, images, and responsive layout in the available browser |
| Word or PDF | Available document/PDF skill and its renderer. In Codex, use the bundled dependency locator when available. In Copilot, use the project's renderer or installed tools; do not assume Codex tools exist. Report a missing renderer instead of claiming visual QA |
| Native Google Docs | Available authorized connector or appropriate native editing skill. If unavailable, prepare a local draft and state the export/import boundary; do not invent connector access |
| API reference | Existing specification and reference generator, plus source and example checks; avoid introducing a second generator |
| Code examples | Existing project tests and safe isolated fixtures, using the documented environment; record expected versus actual behavior |

## Optional validation starter

The [tooling guide](../tooling/README.md) describes explicit commands and prerequisites. The starter configurations live alongside the skill so personal and repository installs both retain them. They are opt-in defaults; they do not override existing project rules or install automatically.

- Vale flags a small set of wordy alternatives. Project vocabulary and approved terminology are more valuable than a large generic rule set. Review suggestions rather than mechanically rewriting them.
- markdownlint-cli2 checks Markdown structure and formatting. Existing project rules take precedence, and long lines are not automatically a readability defect.
- Lychee checks links and anchors. Start with local/offline checks where suitable; external checks send requests and may be affected by authentication, throttling, or temporary failures.
- Playwright plus axe require an explicitly supplied preview URL and a unique visible readiness selector for the completed content. The check captures a rendered page and identifies some accessibility problems only after that signal. It cannot establish complete accessibility compliance or human understanding.

Use tools only on relevant files and changes. Preserve meaningful errors; do not disable a rule merely to obtain a passing result. Explain intentional exceptions and decide whether the rule actually fits this project.

## Settings and integration

Use Copilot's standard agent/skill locations. Keep model selection, terminal approval, workspace trust, and tool authorization under the user's existing controls. No deprecated discovery settings, automatic hooks, broad auto-approval, or mandatory MCP server are needed for this package.

External evidence systems remain optional. Add a connector only when the actual task needs its sources. The agent must distinguish missing access from missing evidence and must not put credentials into the package or project context template.
