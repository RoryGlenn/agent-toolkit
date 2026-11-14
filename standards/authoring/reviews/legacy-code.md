# Legacy-code specialist assessment

Implementation branch: `feat/legacy-code-specialist`, based on
`fa225c1bfc869e374b055beed747147b94eb9333`. Date: 2026-11-13.
Completed source-contract assessment with independent review and separate verification.
Verdict: **`ready_with_limits`** for the authored package and local source/integration
contract. Live model acceptance remains unavailable. This is not external approval or
evidence of improved model performance.

## Intended value and source scope

The specialist addresses a bounded change whose relevant behavior is poorly protected or
whose dependencies obstruct useful feedback. The existing design and writer/reviewer/verifier
roles retain their responsibilities. The new role inherits the caller's settings.

Source identity: Michael C. Feathers, *Working Effectively with Legacy Code*, first edition,
copyright 2005, ISBN 9780132931755, source SHA-256
`2878ffaa3d5a8a3c9128e1c80a90e3d93a3a21a425d0092ce63627a7963e3a1d`.
The complete source study covered 25 chapters, all 24 dependency-breaking techniques and
nested steps, the appendix, glossary, preface/introduction/foreword, and 88 substantive
figures. Private original study remains outside Git. Publishing matter was inventoried;
navigation/index is navigation evidence and cover/logo artwork was excluded as nonoperational.
The public [coverage map](../../../skills/legacy-code-skill/references/coverage.json) records
exact locators, decisions, qualifications, and case-level gaps.

Source examples are not blindly adopted: the supplied Expose Static Method example changes
predicates, other snippets omit context, and some historical language/tool claims require
independent current checks. The guidance preserves bootstrap risk, creation and lifetime,
dispatch, effect/order sensitivity, and the distinction between characterization and an
approved correction. These are source/application judgments, not measured improvements.

## Semantic contract

| Contract | Inspected evidence | Assessment |
| --- | --- | --- |
| T01 job and routing | Actual change/feedback obstacle; adjacent trivial negative case; one owner and shared topic routing | Supported as authored behavior; live selection remains unverified |
| T02 useful mechanisms | Effect tracing, test boundaries, sensing/separation, enabling point, bootstrap, 24 qualified technique choices | Supported by source study and original synthesis |
| T03 grounding | Exact source locators, complete private source/index validation, source-versus-application distinction, explicit missing-source fallback | Supported source contract; live model source consultation remains unverified |
| T04 useful completion | Actionable bounded handoff with actual checks and residual risk; no forced long report | Supported authored contract |
| T05 evaluation | Ten domain cases, two integration cases, trusted correct/wrong controls, explicit execution limits | Supported as authored cases and available evidence, not passing model behavior |
| T06 ownership | Read-only consultation, explicit sole writer, separate review/verification, no recursive legacy dispatch | Supported authored contract; host enforcement/dispatch require separate evidence |
| G01-G04 | Focused discovery, conditional references/source, deterministic helper, thin inherited-settings role | Supported source-level design |

## Shared routing extension reassessment

The changed `task-routing-skill` adds a safe-change outcome and distinguishes it from general
design, data guarantees, documentation, and implementation ownership. Its existing topic
change, bounded consultation, missing-capability and no-delegation policies are retained.
Five new shared routing cases are authored. Selective dependency closure uses the existing
installer/bootstrap mechanisms; no routing service or change to the default profile is added.

This is a source-contract reassessment by the implementation writer. It supports rebinding
the changed entrypoint to its actual bytes, while retaining previous routing observations
at their historical revisions. It does not extend old model runs to the new legacy route.
The new runtime snapshot binds the selected package and resources; fingerprints establish
identity, not behavioral correctness. Independent review remains separately identified.
The previously observed missing-skill discovery/disclosure and protocol-qualification
gap in [routing.md](routing.md) remains open; this extension does not resolve it.

## Deterministic and real-source evidence

- The new helper's 15 focused tests pass on original synthetic EPUBs: complete chapters and
  techniques, nested sections/steps, code/table/image fidelity, continuation, query errors,
  literal punctuation/order, source/index tampering, conflict/idempotence, failed-publish
  rollback, private directory/file boundaries and safe paths.
- Eight focused suite checks pass for declared coverage/case relationships, actual selected
  install and receipt restoration, shared routing preservation, project copying/relocation,
  customization refusal, unchanged default selection, and trusted behavior controls.
- The supplied real EPUB initializes and verifies 25 chapters and 264 indexed entries.
  Complete chapter 4/13 and technique-1 reads, continuation, and original figure inspection
  were checked privately. Source operations remain offline and original bytes are preserved.
- The corrected documented reader flow passes in disposable personal and project fixtures:
  selected install/readback, idempotent initialization, source verification, literal search,
  exact reads/continuations, private asset creation, copied-project relocation and receipt
  restore. The restored receipt is read back and the independent source library survives.
- Native skill validation and package inventory pass. The final checks and their concrete
  environment errors are recorded below; the full required gate is not green.

## Live evaluation readiness and limitations

The proposed matched pilot is LC01, LC02, LC03, LC05, one repetition and two arms: eight
planned actor attempts, with a 180-second actor cap. Original source is absent in both arms.
Configured model/reasoning settings were inspected without exposing credentials:
`gpt-6.1-sol`, `max`. No model or reasoning setting was substituted.

Actual native isolation preflight failed before any actor launched or any credentials
were staged: `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`.
The existing authoring adapter additionally accepts only low/medium/high/xhigh effort,
so the configured max effort cannot be passed through its current interface. No adapter
rewrite, sandbox weakening, privileged host change, or new provider was introduced.

Consequently there are no matched model outputs, grades, usage figures, report scores,
or comparative quality results. An isolated Codex app-server `skills/list` call discovered
both selected skills, enabled, at their actual personal/project paths without a model turn
or credentials. This establishes metadata discovery only. Native named-role dispatch,
live topic-change/ownership/fallback behavior and model source consultation remain unrun.
Missing execution remains unknown, not zero usage, failed advice, or a behavioral pass.

Next meaningful model check: use a host where the existing native isolation canaries pass
and an authoring interface that supports the caller's actual reasoning setting; then run the
declared pilot and integration cases without changing access between arms. Additional held-out
work and repetitions are needed before reliability or improvement claims.

## Final verification and disposition

Independent first-diff review reproduced two required corrections: existing permissive
library/cache boundaries and nonliteral query behavior. It also found that the export
oracle did not constrain a candidate's success audit. The fixes refuse permissive existing
directories without changing them, create assets as 0600 at the initial exclusive open,
perform contiguous case-insensitive literal search including punctuation, and check candidate
success/failure audit effects. The independent reviewer reran the original failure probes
and all 23 focused legacy checks against the corrected bytes: all three findings are
resolved, with no unresolved issue found in that recheck scope.

A separate verifier reran the complete repository checks, corrected reader flow,
real-source tampering/privacy probes and resource identity audit. Both reviewers had
completed complementary original-source study; their combined fidelity review covered
chapters 4–25, while the writer studied chapters 1–3 and supporting matter. They were
separate generic agents, not executions of the new named role. The private reports retain
the initial findings, exact commands, revisions, outputs and bounded recheck scope outside
Git. They do not represent a matched model benchmark or user testing.

| Check | Final observed result |
| --- | --- |
| Focused legacy tests | 23 passed: 15 helper tests and eight suite tests |
| Complete unit suite | 231 tests: 229 passed, two environment errors listed below |
| Ruff lint and format | Passed; 44 Python files checked for format |
| Strict mypy | Passed; 23 source files |
| Native skill validation, authoring structure, pinned upstream verification | Passed; authoring check is structural, not behavioral |
| Package inventory | Passed; 16 skills, seven Codex roles, zero Copilot roles |
| Benchmark correct/wrong controls | Passed; no model campaign |
| Strict OpenSpec and diff whitespace | Passed |
| Disposable selected install, source retrieval, restore and project relocation | Passed with persisted readback; no global rollout |

The two suite errors are
`OracleRegressionTests.test_native_git_inside_repository_stops_parent_discovery` and
`OracleRegressionTests.test_native_grader_cannot_overwrite_protected_alias_target` in
`test_benchmark_revisions.py`. Both stop at the same `bwrap` error above. The verifier
reproduced both on the unchanged original checkout, establishing the host limitation
rather than a new product regression. Neither test was skipped or weakened. This local
assessment precedes hosted CI; separate GitHub delivery results are tracked in
[issue #22](https://github.com/RoryGlenn/agent-toolkit/issues/22) and its linked PR.

### Assessed identities

| Entrypoint | Reviewed SHA-256 |
| --- | --- |
| `skills/legacy-code-skill/SKILL.md` | `ea1159dc06e84ce959f5f53abb6066591d8c1888289cc3bfa998fa908adedeec` |
| `agents/codex/legacy-code-agent.toml` | `3df03b0d0719006a30ed965fb21259b6142034cc19b72e2957d0f8f2e3607da2` |
| `skills/task-routing-skill/SKILL.md` | `2958fd04d1d40dbcf939056658fe615e9f3f717fae9d2fcd0d9eb60b07a7487c` |

The [runtime snapshot](legacy-code-runtime-sha256.json), SHA-256
`28c5f09a8b92b6c7ef79a0980dc3b770c24b3b2b606e0184d6ffd7a806e45f10`,
binds all ten selected skill, routing and role runtime files. Both independent rechecks
verified every entry. The corrected helper is
`93ef28560e5b2d836de572f827f9eb8a3f9f49cf2d235d2910d09246ad62e437`.
These identities establish the assessed bytes; they do not certify behavioral quality.
Historical manifests and model observations retain their original scope.

The skill and role inventory entries are **reviewed** because this assessment is complete.
The live-readiness task remains open. Full acceptance requires a working native isolation
gate and support for the configured effort, followed by the declared pilot and actual
named-role/routing/source-use checks. No reliability, comparative improvement, or measured
speedup is claimed.
