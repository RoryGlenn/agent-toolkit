# Routing evaluation matrix

`cases.json` supplies 14 public development cases and semantic assertions. They are authored
inputs, not results. The new package supplies routing instructions, not a classifier or
persistent agent. Actual selection remains host/model behavior.

## Execute through the host

1. Freeze the toolkit source and actor input identities. Use a disposable personal install
   or portable project bootstrap with the declared selected skills and host roles.
2. Keep this matrix, assertions, grader material and other actors outside the scored actor's
   accessible workspace. Stage only runtime skill resources and required fixture inputs,
   using existing benchmark staging where suitable. Do not use installed evaluation examples
   as the user's product data. Check the actual boundary before a model call.
3. Select the starting role through the host's real mechanism. Send the natural `prompt`
   unchanged; do not add the expected skill/agent name. For `topic-change`, send each entry
   in `turns` as a real subsequent conversation turn, preserving the session.
4. Inspect actual skill reads, role creation, delegated context, tool use and delivered
   outcome. Direct use of the right skill can be correct; do not require a child merely to
   obtain a dispatch counter. To test named specialist selection, use the consequential
   independent-assessment case and inspect actual invocation rather than a final self-report.
5. Independently grade the assertions, including ownership, unnecessary work, failure
   disclosure and loop prevention. Preserve failed/partial attempts and explain settings
   changes before a retry. Report each case/host/model separately.

Revision `routing-development-2` clarifies that the documentation case prohibits executing
the product tool while allowing read-only guidance inspection. The initial blanket command
restriction prevented guidance reads on a shell-only host; retain that earlier attempt as
a constraint limitation, not a model routing failure. A separate consequential-consultation
control tests actual independent specialist execution without injecting a failure.

Selected-install fixtures intentionally omit other domains. `missing-role`, `missing-skill`
and `failed-consultation` define different failure conditions; a missing package is not
successful delegation, and a provider error is not a model reasoning failure. A fabricated
failure described in prose cannot validate actual tool-failure handling.

Use the existing process bounds, permission canaries, role observation and evidence helpers
for native Codex integration. The standalone `skill_authoring` adapter disables children and
stages a single package, so it cannot establish this sibling-dependent multi-agent behavior.
There is no new evaluator service or automatic paid CI campaign in this change.

## Host and model scope

Declare executable/version, model/effort, installed selection, tool availability, actual
settings, deadline, observed usage and input/output hashes. Start with bounded smoke tests,
then repeat representative cases before asserting reliability. Use more than one available
model for the claimed Codex surface; leave unavailable combinations explicit.

| Surface | Current scope | Evidence requirement |
| --- | --- | --- |
| Codex CLI / native roles | Project `.codex/agents` or personal TOML roles; parent permissions | Distinguish loading a role's root instructions in a test profile from actual named-worker dispatch; inspect skill reads and outcomes |
| Codex general project entrypoint | Generated `AGENTS.md` plus selected skills | Actually enable project-instruction ingestion; root role tests do not establish this path |
| Codex IDE surface | Same supported role format where exposed by the installed extension | Editor-specific verification; CLI checks do not establish visible-picker behavior |
| Other skill-capable hosts | Portable skills only; no toolkit-provided agent profiles | Direct skill use only; historical Copilot role trials do not establish a supported adapter |

User direction narrowed the implementation to Codex-only named roles after initial Copilot
experiments. Those attempts must remain historical evidence, not successful current support.
The consequential-consultation control explicitly requests a separate specialist but does
not name DDIA; this tests domain selection and actual dispatch. Simpler natural questions
continue to permit direct skill loading. No universal visible-picker switch is promised.

## Recorded coverage and remaining checks

The [final routing assessment](../../../standards/authoring/reviews/routing.md) and
[sanitized receipt](../../../standards/authoring/reviews/routing-observations.json) distinguish
five observed Astra passes from eight Terra passes plus one partial missing-skill fallback.
These are 14 model/case attempts over ten distinct catalog cases, not execution of all 14
catalog cases on every role/model. Starting specialist profiles use exact root instructions;
general cases use actual generated project guidance. Successful specialist worker dispatch
is separately observed. No GUI picker behavior or universal fallback guarantee is established.

Prioritize the partial missing-skill capability-discovery and qualification gap, then final-
snapshot software-design paths, explicit subtask/failure cases, more topic-change directions
and repeated trials. Keep preceding fault-injection and superseded Copilot trials separate.

## Primary references reviewed 2026-10-30

- [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): standalone
  Codex roles use native delegation and inherit parent permissions/provider configuration.
- [GitHub custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration):
  inspected to establish that this host uses a different role format; its role adapters are
  deliberately not shipped in the current Codex-only design.
- [VS Code custom-agent reference](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference)
  and [subagents](https://code.visualstudio.com/docs/agents/run/subagents): tool interfaces and
  handoff support depend on the selected runtime. Native Copilot delegation and Local handoffs
  are different mechanisms. This change does not configure a universal visible-picker switch.
