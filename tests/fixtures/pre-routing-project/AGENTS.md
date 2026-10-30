<!-- AGENT_TOOLKIT:START -->
## Shared engineering guidance

Use this project's existing architecture, stack, package manager, commands, and
terminology. Existing project guidance remains authoritative within system and user
instructions. Resolve project facts from the repository before applying reusable advice.

Load the relevant installed skill when its task applies:

- Release, package, and documentation verification: [release-and-docs-skill](.agents/skills/release-and-docs-skill/SKILL.md).

For nontrivial engineering changes, assign one source-code writer and use relevant
independent review and verification when delegation is available. Routine tasks do
not need a panel of agents. Follow selected skills' fallback instructions when a host
cannot dispatch a named role; disclose unavailable independent evidence.

Run the project's actual applicable checks and report exact commands and results.
Preserve unrelated work and the user's authorization. Source books and private
studies are optional local resources; disclose missing evidence without claiming it
was consulted. Resolve scripts relative to the skill file that was actually loaded.

Name future reusable instruction packages <task-or-domain>-skill, matching their
directory and SKILL.md name; display names end in Skill. Name Codex definitions
<role-or-domain>-agent.toml with matching snake_case ..._agent identifiers, and
Copilot definitions <role-or-domain>-agent.agent.md with display names ending Agent.
Specialist describes expertise, not an artifact type. Keep host-required SKILL.md
and skill UI metadata agents/openai.yaml filenames unchanged.
<!-- AGENT_TOOLKIT:END -->
