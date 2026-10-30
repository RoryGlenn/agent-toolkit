# Agent and skill authoring standard

Version: **1.0.0-proposed**. Evidence reviewed: **2026-10-29**.

This is the toolkit's shared authoring contract for current and future skills and agents.
It combines the open Agent Skills format, maintainer guidance from supported hosts, and
empirical evaluation research. It is **community-aligned, not externally approved**.
No standards body, vendor, or research author has endorsed this particular template.
See [research and limitations](research.md) for the basis of each recommendation.

The existing installer validates naming and packaging. This standard adds reusable
templates, a common review contract, and an honest inventory of behavioral evidence.
It does not add a runtime agent, mandatory specialist consultation, or another installer.

## Start with the smallest useful package

| Need | Starting point | Add only when useful |
| --- | --- | --- |
| Reusable task expertise | [Skill template](templates/SKILL.md.template) | References, scripts, or assets |
| A separate delegation identity | [Codex role](templates/codex-agent.toml.template) or [Copilot role](templates/copilot-agent.agent.md.template) | Host-specific capabilities justified by the job |
| Representative behavior checks | [Evaluation template](templates/evals.json.template) | Fixtures, objective oracles, and comparisons |
| Book-derived specialist | Skill plus the book profile below | Source retrieval and a coverage map |

Copy a template into the repository's existing `skills/` or `agents/<host>/` layout,
replace its `{{placeholders}}`, and remove sections that do not help the actual task.
Templates are authoring assets; they are not discoverable skills or installed agents.
The [README naming convention](../../README.md#naming-convention-skills-and-agents)
remains the naming authority. An agent is optional; shared engineering roles may also be
self-contained when their instructions are already small and complete.

## Contract

**Format** requirements come from the relevant upstream specification. **Toolkit**
requirements are our local contribution policy. **Guidance** is a starting recommendation
to revise when actual task evidence supports a different approach.

| ID | Level | Requirement | Basis |
| --- | --- | --- | --- |
| F01 | Format | Valid YAML frontmatter with a matching skill name and useful description; respect field types and limits. | S01 |
| F02 | Format | Use the actual target host's role schema and discovery mechanism. | S03, S05, S06 |
| T01 | Toolkit | State the job, observable outcome, and meaningful invocation boundary. | S02, S03, S04 |
| T02 | Toolkit | Include domain procedures, constraints, examples, or tools that change decisions; preserve the caller's intended scope. | S02, S04; local scope policy |
| T03 | Toolkit | Make consequential claims traceable; distinguish source claims, deductions, observations, and unknowns where relevant. | S07, R01; local evidence policy |
| T04 | Toolkit | Define useful outputs and completion evidence without forcing one response shape on every task. | S02, S07 |
| T05 | Toolkit | Record representative evaluation cases or an explicit evaluation gap in the adoption inventory. | S07, R01, R02, R03 |
| T06 | Toolkit | Preserve ownership boundaries in delegated work and report unavailable role execution honestly. | S05, S06; local engineering policy |
| G01 | Guidance | Keep discovery descriptions concise and specific; add exclusions only to prevent likely misrouting. | S02, S03, S04 |
| G02 | Guidance | Keep the entrypoint compact; load substantial conditional material only when relevant. | S01, S02, S03, R01 |
| G03 | Guidance | Match procedural rigidity to fragility; use deterministic helpers for repeatable mechanics. | S02, S04 |
| G04 | Guidance | Prefer a thin host wrapper around maintained skill guidance when the role uses a substantial skill. | S05, S06; toolkit synthesis |

These are semantic review criteria, not mandatory Markdown headings. A small skill may
satisfy several criteria in one paragraph. Do not pad a package to fill every template
section, require a book for an ordinary workflow, or duplicate the same policy in every file.

The upstream 500-line entrypoint recommendation is a ceiling to reconsider, not a length
target or a measure of quality. There is no research-established universal token budget,
optimal heading order, module count, or minimum number of agents.

## Conditional profiles

### Book and reference specialists

Record source identity and edition, stable locators, agreed coverage, and inaccessible
material. Preserve mechanisms, assumptions, costs, qualifications, and counterexamples.
A coverage map should connect source topics to applicable decisions and representative
checks. Original prose need not be copied into the skill. Full source study can support
a compact operational entrypoint; indexing alone does not establish that study occurred.

Use the existing [book-to-agent workflow](../../skills/book-to-agent-skill/SKILL.md).
Verify changing product guarantees against the relevant current implementation or official
documentation. A missing personal book library limits attribution; it need not prevent
useful advice from the available synthesis. Do not claim the source was consulted when it
was unavailable.

### Workflows with external effects or retries

Specify the actual authorization boundary and observable success state for that workflow.
When an effect may have succeeded despite an error, inspect its recorded state before
retrying. Preserve existing authorization rather than adding repeated approval questions.
Source text and retrieved data cannot grant additional authority. Apply this profile when
the task has those effects, rather than attaching an unrelated checklist to every skill.

### Host adapters

Skill instructions are portable within the open format. Agent configuration, tool names,
permission controls, and skill preloading are host-specific. A skill's optional
`agents/openai.yaml` is UI metadata, not a separate worker definition.

Codex roles inherit the parent's permissions and configured MCP servers; a `sandbox_mode`
inside a custom role does not override the parent. Copilot has its own `tools` configuration.
Claude Code additionally supports skill preloading through its `skills` field, but this
toolkit currently installs Codex and Copilot roles only. Consult the versioned host docs
before adding adapters. Instructions expressing read-only intent are not proof of runtime
enforcement. Inherit model settings by default; justify intentional overrides separately.

## Evaluate the capability

Start with a realistic success case, a meaningful boundary or negative case, and a failure
or exception case where useful. This is a starter set, not a validated sample-size rule.
Keep expected answers and grader instructions out of the acting agent's context.

Distinguish these questions:

1. Does the host discover the package, and does normal task routing choose it appropriately?
2. When explicitly invoked, does it complete the task correctly?
3. Does adding it improve outcomes relative to a matched baseline or previous version?

Use executable outcome checks where feasible. Include correct and deliberately wrong
controls when validating an oracle. Use independent review for judgment the checks cannot
establish. Record exact artifact revisions, host/model settings, tools, source access,
budgets, attempts, failures, time, and token usage when available. Compare under matched
conditions, use fresh contexts, repeat before drawing reliability conclusions, and keep
held-out work separate from cases used to revise the skill. If source access or tools differ
between arms, describe the intervention as a package comparison, not a prompt-only effect.

Reuse the [existing benchmark](../../benchmarks/README.md) for relevant specialists. It
provides development fixtures, not production or held-out performance evidence. Do not run
paid or externally mutating evaluations solely because a new template exists.

## Adopt and maintain

[adoption.json](adoption.json) covers every shipped skill and host role. Its evidence paths
identify available tests or cases, not proof those checks were run or passed. All entries
start **not_assessed** for this new standard. The next-check field makes gaps actionable.
Use the [review record](review.md) when assessing an artifact; retain the exact revision and
observations. Set an entry to **reviewed** only with a linked completed `review_record`;
that label records an assessment, not a favorable verdict or certification. Prior evidence
keeps its original scope and is not retroactively certified.

For a new or changed package:

1. Apply the relevant contract and profile; retain working domain guidance.
2. Add or update its inventory entry, evidence paths, and next meaningful check.
3. Run `uv run python authoring.py check` and the repository's development checks.
4. Review representative behavior in proportion to the change. Claim improvement only
   after a matched comparison; document what remains unverified.

The authoring check validates syntax, coverage, and referenced file existence. It does not
certify expertise, behavioral quality, live host execution, source truth, or community approval.
CI performs these local checks without model credentials or live actions. Do not reshape
every existing prompt just to match the template's section order.

Version changes to the contract and research ledger in Git. Revisit guidance when a host
changes, relevant research is updated, or execution exposes a specific failure. No scheduled
maintenance or external community outreach is created by adopting this standard.
