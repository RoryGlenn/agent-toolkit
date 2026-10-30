# Shared routing assessment, issue 13

Source baseline: `a143ea86a7a0e6fa4ce15ca3fecfe57b30aba308`. Assessor: implementation
agent, 2026-10-30. Independent review and bounded execution evidence are recorded below.
Verdict: **ready_with_limits** for the source contract. The observed missing-skill case is
partial, not a passing fallback; general routing reliability and GUI behavior remain unverified.

## Intended value and design

The selected specialist is a useful default, but must not force an unrelated question
through the wrong procedure. One shared `task-routing-skill` now owns the routing contract;
there is no new routing agent, service, classifier, model default or global configuration.
Existing source distribution only installs skill packages and role files, so the small
shared package reuses dependency closure rather than adding a second ownership mechanism.

Every existing skill has a compact conditional pointer, and every role checks top-level
scope before its domain-specific procedure. Trivial requests bypass routing ceremony;
assigned subtasks return to their owner. Missing roles/tools use direct skills; missing
skills permit only bounded available expertise with honest disclosure. Mixed work retains
one owner and at most one cross-domain consultation level, with visited roles and ownership
included in the handoff. This is model instruction, not a deterministic loop-enforcement service.

The user subsequently requested a single agent-definition format, with Codex-only roles if
Codex and Copilot definitions could not be unified. They use different host schemas, so this
implementation keeps only six Codex TOML roles. All Copilot wrappers and their authoring
template are removed; no generator or second profile format replaces them. The existing
Copilot install target remains skill-only for backward-compatible portable guidance.

Existing Codex model and permission-related fields are preserved. Host permissions remain
the caller's responsibility; delegation does not imply that the visible picker changed.
An explicit project update removes old Copilot role copies only under the existing ownership
hash checks. Personal installs do not delete existing global wrappers; their retirement
requires the old restoration receipt or a deliberately scoped migration.

## Semantic assessment

| Contract | Assessment and inspected evidence |
| --- | --- |
| T01 job/routing | supported: per-turn outcome selection, domain table, trivial negative case, and assigned-subtask exception in shared policy and entrypoint pointers |
| T02 useful procedure | supported: direct skill versus bounded consultation, mixed-task ownership, missing-capability fallback and retry/loop limits; existing domain guidance preserved |
| T03 grounding | supported: actual skill reads/role events required; product facts cannot come from skill examples/evals; source/provider/host guarantees are qualified |
| T04 output/completion | supported: current owner waits, checks the result against the original request and delivers useful content instead of merely announcing transfer |
| T05 evaluation | supported as authored cases and explicit gaps: 14 public routing cases plus packaging regressions; case existence does not establish a passing model result |
| T06 ownership | supported: explicit no-delegation, one writer, read-only requests and assigned subtask scope preserved; no silent model/provider/permission changes |
| G01–G04 | supported where applicable: small shared runtime owner, conditional loading, no panel for routine tasks, thin host wrappers with existing domain skills |

These source findings apply to all 21 entrypoints identified below. Prior domain assessments
remain at their original hashes in the documentation, DDIA, software-design and engineering
records. They are not silently rebound to these changed entrypoints. The new routing skill has no prior behavioral claim; the removed Copilot roles are
historical evidence only. The old `runtime-sha256.json` and observation
receipt are preserved as historical evidence; current source identities are in
[routing-runtime-sha256.json](routing-runtime-sha256.json).

## Compatibility and executable checks

Personal installs remain selected and reversible; routing is an automatically included
shared dependency, not automatic installation of other domains. Bootstrap compares the
requested dependency closure with the expanded prior selection. This adds newly required
dependencies during an explicit `--update`, retains all prior selected packages, and still
rejects unrelated skill/host changes. Existing owned hashes, collision checks, dry runs and
rollback behavior remain in force. A restore preflight now refuses removal of a shared
skill or role required by a surviving managed skill from the same canonical source, including cross-receipt routing,
DDIA and shared engineering-role consumers. Other checkouts and unmanaged copies are not assigned
current dependency semantics merely because their names match. Restore dependent installations first. Existing
backup restoration and source-missing skill-only cleanup remain supported; this guard does
not certify compatibility of a restored historical backup.

`tests/fixtures/pre-routing-project` is real output from the baseline installer archive.
`tests/test_routing.py` upgrades that old manifest and checks relocation/no-op, refusal of
edited managed files/unmanaged routing collisions, rejection of unrelated selection changes,
selected Copilot skill-only installation and hash-protected retirement of legacy project roles, missing dependencies and independently owned link restore.
Existing unit tests retain their original behavioral assertions with expected new dependencies
and role counts updated. Actual run results are recorded below only after execution.

## Evidence boundaries

The [case matrix](../../../skills/task-routing-skill/evals/README.md) targets Codex named
roles and the general project entrypoint. The single-package authoring adapter cannot
establish sibling dependency or multi-agent routing behavior. Live tests must use natural
requests and observed skill/role events. Loading a role's instructions into a root test
profile differs from actual named-worker dispatch; both must be labeled accurately. The
general entrypoint needs real generated AGENTS.md ingestion. A prompt with two paragraphs
is not a two-turn conversation. Missing packages, unavailable tools, provider failures and
reasoning failures remain distinct outcomes.

CLI checks cannot establish GUI behavior or a visible-picker switch. Any untested host/model
combination remains unverified. Earlier Copilot experiments remain retained historical
attempts from the superseded design, not current supported-role claims. Existing authoring
adoption evaluations keep their original identities and scope.

## Execution observations

The implementation agent ran the unmodified baseline from a separate archive of `a143ea8`:
190 tests passed in 27.965 seconds. An earlier unsealed worktree attempt overlapped initial
scaffolding and is not used as baseline evidence. The isolated archive result establishes
the baseline without relying on concurrently edited files.

## Final Codex-only source checks

After the user narrowed named roles to Codex, the implementation agent ran the full suite:
**203 tests passed in 28.547 seconds**. The 45 installer tests, 13 routing tests and 21
bootstrap tests also passed separately. Ruff lint/format, strict mypy (22 source files),
authoring inventory (21 artifacts), package validation (15 skills/six Codex/zero Copilot),
upstream verification, new routing-skill validation and diff checks passed. The public
benchmark's 13 reference/wrong-control phases passed on this final scope. Current runtime
identity checks match all 80 recorded files. These source checks do not establish model routing.

## Independent final verification

A separate reviewer cleared the source after the shared-dependency restore, foreign-source
consumer and Codex-only retirement corrections. A separate verifier ran the final source
suite: **203 tests passed in 28.167 seconds**. The following commands passed on that source:

- `uv sync --frozen --group dev`
- `uv run python -m unittest discover -s tests -p test_routing.py -v` (13 tests)
- `uv run python -m unittest discover -s tests -p test_install.py -v` (45 tests)
- `uv run python -m unittest discover -s tests -p test_project_bootstrap.py -v` (21 tests)
- `uv run python -m unittest discover -s tests -v` (203 tests)
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy`
- `uv run python authoring.py check`
- `uv run python -m skill_authoring verify-upstream`
- `python3 install.py check`
- `uv run python -m benchmarks validate` (13 reference/wrong-control phases)
- `git diff --check`

A fresh regular-file source copy passed **45 CLI operations** covering both-target selected
and full installs, same-source shared-dependency restore refusal and correct reverse order,
foreign pre-routing installation preservation, old personal Copilot wrapper preservation,
legacy project role retirement, edited-owned/unmanaged-collision refusal, unrelated content
preservation and relocated project no-op. All 21 entrypoint and 80 resource identities matched;
all six Codex roles retained their noninstruction settings. Seven historical domain review,
evidence and manifest files remained byte-identical. These are mechanical guarantees within
the tested environment, not behavioral certification of the model instructions.

## Final Codex routing observations

[routing-observations.json](routing-observations.json) contains sanitized frozen identities,
settings, outcomes, independent grades, observed reads/dispatches and artifact hashes. Raw
traces, private paths, credentials, session identifiers and full model reasoning are excluded.
A digest identifies a retained local artifact; it does not make that artifact independently
inspectable from this repository alone. Cases are public development inputs, not a private
held-out study or a comparison proving routing improvement.

The final macOS arm64/Codex CLI `0.165.0` matrix contains **14 model/case attempts over ten
distinct catalog cases**, totaling **15 user turns**, with a 180-second bound per turn and
high reasoning effort. One separate reviewer graded actual outputs and tool traces. Case
coverage differs by model; the following counts are not a model ranking:

| Model | Observed cases | Result |
| --- | --- | --- |
| `gpt-6-astra` | Documentation → data, data → documentation, general project entrypoint, consequential consultation, two-turn topic change | Five of five passed the scoped assertions |
| `gpt-5.6-terra` | Both directions, general project entrypoint, consequential consultation, mixed recovery guide, trivial request, no delegation, missing role, missing skill | Eight of nine passed; missing skill remained partial |

Most starting specialists use their exact role instructions loaded into a root developer-
instruction test profile. That tests the role policy, not native visible-picker selection.
The general-entrypoint cases instead enabled actual generated `AGENTS.md` ingestion. Direct
routing was established by real target-skill reads, not a final assertion that expertise was
used. The two-turn case used a real subsequent conversation turn. No evaluation-fixture reads
or product command execution/mutation were observed in these final cases.

Both models also made an actual successful `ddia_agent` child call for the separate-specialist
control, and the child read its DDIA guidance. The observed child model matched the parent.
That prompt requests a separate specialist without naming DDIA, so it tests domain selection
and dispatch under an explicit consultation request; it does not prove spontaneous delegation
for every consequential question. Exact NEW_TASK assignment text was encrypted in the retained
trace and was not independently inspected. The original question, scope, returned outcome and
absence of grandchildren were observed through available parent/child records. Children inherit
parent history; this is not blinded or clean-context independent review. Root token observations
are recorded, but aggregate descendant tokens and cost remain unknown.

### Partial missing-skill fallback

In Terra's documentation-only installation, the missing-skill case correctly rejected the
claim that quorum overlap alone guarantees linearizability and did not fabricate skill reads
or specialist dispatch. It made no tool calls, did not discover or disclose the absent DDIA
capability, and left relevant assumptions out of its protocol examples. This result is
**partial_fallback_not_established**, not a passing routing or fallback result. No installation
or permission change occurred. The next meaningful work is improving and retesting capability
discovery/disclosure and qualified reasoning when the required skill is absent.

The successful missing-role case is a different condition: its skill existed and was actually
read. It does not erase the missing-skill gap. Do not infer that all fallback paths passed or
that every selected role/model will follow the policy.

### Preceding and unverified evidence

One earlier Astra fault control attempted a real DDIA child with an intentionally unsupported
model and received `model_not_found`; it then read DDIA guidance directly and disclosed the
failed consultation. The receipt retains this as preceding-snapshot evidence, not a final-
runtime failure-handling pass. Earlier command-constraint corrections and unsuccessful
Copilot experiments likewise keep their original scope. Copilot named-role work was superseded
by the user's Codex-only decision and is not current supported-agent or GUI evidence.

Final-model coverage is not the full role × case × model matrix. In particular, software-design
starting-role and documentation-to-design cases, assigned-subtask/misrouting controls and the
fault-injection case still need final-snapshot execution. The topic-change observation is
Astra-only; other directions and repetitions remain open. No GUI picker change, arbitrary-model
compatibility, original-book retrieval, production correctness, universal loop prevention or
general routing reliability is established by these bounded observations.

## Corrections after initial review and live checks

Independent review identified reverse-order personal restoration removing the shared routing
link while a later skill remained installed. The restore preflight now checks current
surviving dependencies before mutation; new both-host tests cover that sequence, existing
DDIA dependencies, shared engineering roles and dangling-source cleanup. A second review correction scopes
consumer recognition to exact canonical-source links, including dangling links. Both-host
regressions replay real baseline receipts to preserve older foreign-source skills/roles/receipts. The 45 existing installer tests also passed after this correction. Existing backup
refresh/symlink rollback behavior remains unchanged. At that intermediate stage both role templates qualified their own skill load by domain;
the final scope retains only the corrected Codex template.

Initial Copilot attempts answered from general knowledge without reading the intended
skills. Startup clarifications were trialed before the user narrowed scope; those wrappers
are now removed. The shared policy still distinguishes data-correctness explanations from
reader-facing artifacts. Copilot trial receipts remain historical; none establishes current
named-role support on that host.

The final host simplification also removes the Copilot template and rejects accidentally
reintroduced Copilot role files during package validation. Historical project manifests
remain recognized so unchanged owned roles can be retired safely; edited or unmanaged roles
are preserved or cause explicit refusal. Baseline-receipt fixtures remain historical data,
not shipped agent definitions.

The data-to-documentation case's original blanket command prohibition prevented shell-based
file reads on Codex. Its revised constraint permits read-only inspection but forbids running
the product tool. This is a recorded case correction, not evidence that the original run
succeeded. The new consequential consultation control tests actual independent dispatch.

## Current entrypoint identities

| Artifact | SHA-256 |
| --- | --- |
| `agents/codex/adversarial-reviewer-agent.toml` | `7318cdb29d3e4932b870053e2fc6ed8fb2ba070ccbe2bef268409b010e7ea050` |
| `agents/codex/ddia-agent.toml` | `dc45edadd59d19f978928abd9aee74fc7ddb6a317f8085da0f7e1f7c4eb3f538` |
| `agents/codex/documentation-agent.toml` | `7f703acc348420a78336864199ab7190f18313b1f008b7b1846000b396096cb0` |
| `agents/codex/implementation-owner-agent.toml` | `922010ffcb32091f8c1f3f91b49f06eea32d694b7350a49ad6f2286950b7ddc6` |
| `agents/codex/software-design-agent.toml` | `f4541a0559aea670fa55ce7bc7c2dafc6a4ac84802abc21ed67c37e3e00a786e` |
| `agents/codex/verifier-agent.toml` | `fa9f3615306b784e071dca0785f84f99e395e53410bc7239bbe908f8a09e840a` |
| `skills/ddia-assess-skill/SKILL.md` | `6e68360c2e067f0193d65b7a87b9625d5ea7fcaab9579849ea6e4999717756f1` |
| `skills/ddia-design-skill/SKILL.md` | `8e3e34fe0e351ffee0c292f4ccb9217fabc34acc1a721c8bcffbe7db9756c9c5` |
| `skills/ddia-explain-skill/SKILL.md` | `9bfee8bce34bd746ad1ca9fd2acbd7e8e9d8c9663d15dcc12e166925590a181f` |
| `skills/ddia-migrate-skill/SKILL.md` | `b0f8077a47fc4901e8c8b2c609e74e5c5801948bcfbd7f634d1ddb492e7c3cdd` |
| `skills/ddia-operate-skill/SKILL.md` | `38e176029708ca9dbcf9e19763a8099d2cfca2f3d3ff3678f0fffe1027a64992` |
| `skills/ddia-review-skill/SKILL.md` | `f1d7fd26e08baf211158c189f9e4a4d5e4d2f0dcf67c05cbf8652f28ba049dac` |
| `skills/ddia-skill/SKILL.md` | `bc1c5f3fb907173206360537892d90fda1116091e48f743364962b55ef12d013` |
| `skills/ddia-validate-skill/SKILL.md` | `d8cf529b70bc9161e8238ec23aa88fc9c528784626d9dbf1e56c8c499c9b6aa8` |
| `skills/documentation-skill/SKILL.md` | `94b7bcbb5755db1199d61580f20e0ab3602f054bc7f866e76fd21c803deb2bf0` |
| `skills/independent-diff-review-skill/SKILL.md` | `d3b22697c802b4b10af4173ab0d57088107e2eacb5eee30500e50ad690351f99` |
| `skills/issue-to-tested-pr-skill/SKILL.md` | `8a4c94f77ced91f1b9cfe45de1a8b6535c85930ef1c65fbd4b9fc64f06885cb5` |
| `skills/release-and-docs-skill/SKILL.md` | `533e30cc3c30abcce294fb0fb5f73692b8168b481990c60b5187b59e22f7980b` |
| `skills/simplify-or-delete-skill/SKILL.md` | `e17d3a9f815484a912f18b269c1400195d72efdcb822b27661e8f94c899a42d9` |
| `skills/software-design-skill/SKILL.md` | `dcd947d581971024c3870d1d78a95b8fced1c2a587451eeda44fe4425f34c264` |
| `skills/task-routing-skill/SKILL.md` | `cac5c86f197b564060cd7b21ae3d43eac1089ebe335eb43a832fd57f013fbff8` |
