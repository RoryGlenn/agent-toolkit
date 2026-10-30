# Upstream skill authoring on Codex

Use the open [Agent Skills format](https://agentskills.io/specification), OpenAI's native
Codex scaffolder, and Anthropic's evaluation workflow. This package has no dependency on
the toolkit's existing custom skills, agent roles, or benchmark implementation. It does
not install or invoke them. Its Python dependencies are the standard library and PyYAML
for OpenAI's native helpers, already in the repository's development environment.

## Sources and attribution

[UPSTREAM.json](UPSTREAM.json) pins exact upstream revisions and Git blob hashes.
`upstream/openai/` contains the unmodified Codex skill-creator instructions, initializer,
UI metadata generator, validator, Apache-2.0 license, and NOTICE from OpenAI's Codex repository.
`upstream/anthropic/` contains the unmodified skill-creator workflow, grader/comparator/
analyzer instructions, schemas, aggregation and static review tools, and Apache-2.0 license.
These files retain their original licenses; they do not assign a license to this repository.
The adapter and this guide are local integrations, not vendor-endorsed implementations.

Source revisions reviewed 2026-10-29:

- OpenAI Codex: `55c099a142eb302188fee00ab9e9062f2db1c359`.
- Anthropic skills: `ca45fc496a3436251f191354091d557da31c15b5`.
- Agent Skills specification repository: `69ef37e9424c0a7ea9dd2293b559e43ec8176379`.

Verify the snapshot with `uv run python -m skill_authoring verify-upstream`. Update vendored
files deliberately from a reviewed upstream revision, retain notices, and update their
manifest hashes. Formatting and type checks exclude upstream files to preserve exact bytes;
integration tests execute the helpers. Native helpers are not substitutes for the format
specification: for example, this pinned OpenAI quick validator rejects `compatibility`,
although the open format supports it. Do not remove legitimate metadata to satisfy that helper.

## Create the skill

From the repository root on macOS or Linux:

```bash
uv run python -m skill_authoring scaffold example-skill --path /path/to/project/skills
```

This executes OpenAI's initializer, including its `agents/openai.yaml` generator. It refuses
an existing destination. Add `--resources references,scripts` only when those resources
have an actual purpose. The generated TODOs are intentional authoring placeholders: replace
them with task-specific expertise before evaluating or shipping. Read the pinned
[OpenAI authoring instructions](upstream/openai/SKILL.md) for scope and reference guidance.
No dedicated custom agent is needed to author the skill.

Check completed scaffolding with:

```bash
uv run python -m skill_authoring validate /path/to/project/skills/example-skill
```

That command runs the native quick validator, with its stated limitations. The repository's
`authoring.py check` separately checks its portable metadata and contribution inventory.

## Evaluate and improve

Follow the pinned [Anthropic workflow](upstream/anthropic/SKILL.md) through intent, draft,
realistic cases, paired execution, grading, human review, and revision. Its Claude-specific
runner commands are replaced by this package's Codex adapter. Do not execute those original
Claude commands and interpret them as evidence of Codex behavior.

1. Create `evals/evals.json` using the [upstream schemas](upstream/anthropic/references/schemas.md).
   Use a few realistic success, boundary, and exception cases to start. Each case needs an
   integer ID, prompt, expected output, input files, and checkable `expectations`. Input paths
   are relative to the skill root. The alias `assertions` is accepted for the upstream guide's
   alternate spelling. Expected outputs and expectations remain controller-only.
2. Run fresh paired Codex sessions with the skill present and absent, using the same model,
   effort, inputs, and deadline. The default is three repetitions. The adapter alternates
   arm order between repetitions and runs sequentially to bound concurrent usage.
3. Grade every run against actual outputs and traces, using executable outcome checks when
   feasible. Otherwise give a fresh reviewer the upstream [grader instructions](upstream/anthropic/agents/grader.md),
   assertions, and artifacts. Keep the author's intended answer out of its context. Save the
   upstream `grading.json`, including evidence for every expectation and consistent counts.
4. Generate a static review page and benchmark. Inspect results with the user, including
   failures and time/token costs. For subjective differences prepare a blind A/B bundle and
   give a fresh reviewer the upstream comparator instructions plus only that bundle.
5. Revise from observed problems, retain the old outputs and version, then repeat in a new
   iteration directory. Hold out fresh cases before claiming general improvement.

Execution is explicit and uses the existing signed-in Codex CLI, not API keys or a new
provider account. Select a regular Codex `auth.json` with `--auth-source`; never put its
contents in prompts. The CLI may use account quota. A run performs two sessions per case
per repetition. There are no automatic retries or background evaluations.

```bash
uv run python -m skill_authoring run /path/to/example-skill/evals/evals.json \
  --skill /path/to/example-skill --output .skill-evals/iteration-1 \
  --model MODEL --effort medium --repetitions 1 --seconds 180 \
  --auth-source /absolute/path/to/codex/auth.json

# After independent grading has produced every grading.json:
uv run python -m skill_authoring report .skill-evals/iteration-1
uv run python -m skill_authoring blind .skill-evals/iteration-1 \
  --destination .skill-evals/blind-iteration-1
```

The static `review.html` uses Anthropic's actual viewer and can be opened locally. The
adapter supplies recursive output data through its rendering functions, retaining original
relative display names without creating flattened filesystem names. Embedded JSON is escaped
so artifact text cannot terminate the viewer's script element. Original output trees remain intact. It does
not start a server. Reviewer feedback downloads as JSON; preserve it with the iteration.
Keep `blind-map.json` outside the reviewer's supplied bundle. A/B labels hide arm identity,
but output content itself can sometimes reveal its source. Blind review is not guaranteed
anonymity. The comparator bundle excludes executor traces; use the grader for process claims.

## Execution and evidence boundaries

Each attempt gets fresh input copies, its own Git root, a separate home and Codex client configuration, and
only the candidate's standard runtime resources (`SKILL.md`, `agents/openai.yaml`, `scripts`,
`references`, `assets`). Curator `evals/`, grader role files, and unrelated installed skills
are not staged. Runtime executable modes are preserved and recorded in the plan.
Nonstandard runtime directories need a reviewed adapter extension.
The baseline has no skill package, so this measures the package intervention, not just prose.

The native tool profile denies reads outside the attempt's declared runtime and workspace,
denies tool network access, and disables child agents, plugins, apps, and memories. Positive
workspace and negative controller, alias, write, and network canaries must pass before
credentials are copied or a model is launched. The Codex client can still contact its model
provider. If the native sandbox is unavailable, setup fails explicitly; there is no fallback
to unrestricted execution. Credentials are removed after every attempt.

`invocation: "implicit"` is a local evaluation extension for natural routing and negative
cases. Otherwise the with-skill actor is explicitly asked to use the skill. Assess implicit
activation from real traces; the adapter does not count self-reported skill usage as proof.
It does not implement automatic description optimization or launch grader models for you.

Every planned attempt has a status record, including failed setup and timeouts. Reporting
refuses incomplete, missing, ungraded, or inconsistent paired data. Root-turn token usage is
observed from Codex events; child agents are disabled. Missing usage remains unknown and blocks
the upstream numeric report, rather than becoming zero or output-character counts. The adapter
also corrects upstream's fixed three-repetition metadata to the actual run count and uses
controller timing instead of grader-supplied timing. Upstream source files stay unchanged.

Tests use newly created fixture skills and simulated Codex responses. They establish adapter
and upstream-tool integration, not live model quality or improvement of existing custom agents.
Live execution additionally requires working native isolation, connectivity, and selected
credentials. No live or paid evaluations are part of deterministic CI.
