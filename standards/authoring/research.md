# Research and community basis

Reviewed 2026-10-29. This ledger separates format specifications, maintainer recommendations,
empirical findings, and our own design choices. Agreement among sources supports a starting
practice; it does not confer external approval on this package or establish a perfect template.

## Primary sources

| ID | Source | Type | Contribution and limit |
| --- | --- | --- | --- |
| S01 | [Agent Skills specification](https://agentskills.io/specification) | Open format | Frontmatter, optional resources, progressive disclosure. The body has no mandated section structure; a 500-line entrypoint is a recommendation. |
| S02 | [Agent Skills creator practices](https://agentskills.io/skill-creation/best-practices) | Community-maintained guidance | Real expertise, coherent scope, selective references, and refinement through execution. Guidance rather than a controlled experiment. |
| S03 | [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) | Host-maintainer guidance | Discovery, descriptions, optional UI metadata, and explicit/implicit invocation. Applies to supported OpenAI hosts; discovery details can change. |
| S04 | [Anthropic: Skill authoring practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Host-maintainer guidance | Concision, control proportional to fragility, progressive disclosure, and testing. Does not validate our particular wording. |
| S05 | [GitHub: Custom agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) | Host reference | Copilot YAML profiles and tool configuration. Some properties differ across GitHub and IDE surfaces. |
| S06 | [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Host reference | Codex TOML roles, inherited settings, and focused responsibilities. A syntactically valid file is not execution evidence. |
| S07 | [Agent Skills: Evaluating output quality](https://agentskills.io/skill-creation/evaluating-skills) | Community-maintained method | Realistic cases, baseline comparisons, fresh contexts, traces, objective checks, and human review. Examples are starter procedures, not universal statistical guarantees. |
| S08 | [Claude Code: Custom subagents](https://code.claude.com/docs/en/sub-agents) | Host reference | Separate context, role routing, tools, and skill preloading. Used to explain portability boundaries; no new Claude installer support is claimed. |
| S09 | [OpenAI native skill-creator](https://github.com/openai/codex/tree/55c099a142eb302188fee00ab9e9062f2db1c359/codex-rs/skills/src/assets/samples/skill-creator) | Pinned implementation | The actual initializer, UI metadata generator, and quick validator are vendored without modification. The blank template is extracted from that initializer. Validator behavior is narrower than the open format in some cases. |
| S10 | [Anthropic skill-creator](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/skill-creator) | Pinned implementation and workflow | Actual grading/comparison prompts, schemas, aggregation, and static viewer are reused. The separate Codex adapter supplies execution and strict result checks. Existence of evaluation tooling is not proof of improved model performance. |
| S11 | [AAIF: Agent Skills](https://aaif.io/blog/agent-skills-sharing-team-expertise-across-ai-agents), 2026-10-22 | Foundation announcement | Agent Skills now has neutral multi-company governance under AAIF. This establishes community governance of the format, not endorsement of our adapter or domain instructions. |

The open format's [maintained repository](https://github.com/agentskills/agentskills)
describes open contributions and cross-client use. Independent documentation from OpenAI,
Anthropic, and GitHub establishes practical cross-vendor alignment. This evidence supports
the term **community-aligned**. We have not obtained an external review or endorsement of
the toolkit's local requirements, templates, or validator.

The selected implementation is now S01 + S09 + S10. See the independent
[authoring package and provenance](../../skill_authoring/README.md). Its integration does
not invoke or reuse Rory's existing custom skills, agents, or evaluation implementation.

## Empirical evidence

| ID | Study and pinned version | Result relevant to this design | Limits |
| --- | --- | --- | --- |
| R01 | [SkillsBench, arXiv:2602.12670v4](https://arxiv.org/abs/2602.12670v4), revised 2026-06-14 | Reports matched evaluation of 87 tasks across 18 model/harness configurations: average pass rate 33.9% to 50.5%, a 16.6 percentage-point gain. Focused bundles performed better than larger exhaustive ones in its analysis. | Expertise-heavy task selection and tested configurations limit transfer. The size comparison does not establish a causal universal module limit. Earlier versions reported different inventory and aggregate figures; do not mix them. |
| R02 | [SWE-Skills-Bench, arXiv:2603.15401v2](https://arxiv.org/abs/2603.15401v2), revised 2026-10-27 | Across 98 skills and four model/harness configurations, 92 skills had no statistically significant effect. Average verifier pass ratio rose from 76.6% to 76.9%. Helpful cases supplied omitted procedures; harmful cases overrode task instructions through template anchoring. | Requirements were synthesized from skills, verifiers were generated, and each task ran once per condition/configuration. These choices limit transfer to natural requests and reliability claims. No detected effect is not proof of no utility. |
| R03 | [Evaluating AGENTS.md, arXiv:2602.11988v3](https://arxiv.org/abs/2602.11988v3), revised 2026-09-29 | Reports no general task-success improvement from repository context files and over 20% average inference-cost increase in its settings. Nonstandard project practices can still warrant explicit instructions. | Studies repository context files, not this skill template. It supports caution about unconditional context, not a conclusion that selective skills cannot help. |

These results are not pooled: they study different interventions, tasks, and configurations.
R02's earlier [v1](https://arxiv.org/abs/2603.15401v1) used a smaller inventory and different
aggregate figures; the row above uses v2 consistently.
None tests this toolkit's new standard or proves that adopting these templates improves
Rory's projects. The defensible inference is to evaluate domain fit, version compatibility,
actual outcomes, and overhead locally before making improvement claims.

## Local choices and disagreements

- Required `-skill` and `-agent` suffixes are existing toolkit conventions, not the open
  format's required suffixes.
- The contract's exact rule IDs, inventory JSON, review record, and template sections are
  local maintenance choices. They are not upstream schemas or a research-validated recipe.
- A thin role wrapper is our default for a substantial shared skill. Small self-contained
  roles remain valid. Extra files, reference routers, agents, or scripts need a concrete job.
- A starter success/boundary/failure set helps expose assumptions. It does not establish
  an adequate statistical sample for all domains. The existing benchmark remains available.
- Instructions can guide ownership and authorization but cannot themselves enforce tool
  permissions. Configure and test the actual host for any enforcement claim.
- Evidence paths in the inventory establish that materials exist. Quality and completion
  require inspecting execution and results. The checker never upgrades evidence status.

## Refresh procedure

Check the official format and target-host pages when changing a relevant field. Preserve
the versioned research links above and note later revisions separately. When a new paper
or community recommendation conflicts with a rule, compare scope and methods before
changing the contract. Record the observed task failure or evaluation that motivates a
local change. Web pages are mutable snapshots checked on the date above; the retrieval date
does not make their future contents immutable.
