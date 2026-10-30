# Adoption review, 2026-10-30

The 14 skills and seven host roles were assessed against authoring standard
`1.1.0-proposed`, starting from commit
`156ca63e5bbc1a76205c24d919a3d9b4d3c13d36`. This is a source-level assessment by the
implementation agent, with independent review and live observations recorded separately
in the [execution evidence](evidence.md) and [sanitized receipt](observations.json). It is not external certification or a claim of improved agent performance.

The [inventory](../adoption.json) binds each entrypoint to its exact `reviewed_sha256`
and links its completed group record. These hashes identify the reviewed entrypoints,
not entire dependency trees. The [runtime manifest](runtime-sha256.json) records exact
SHA-256 identities of skill package resources, including optional documentation tooling,
plus the seven host-role files. This inventory excludes evaluations and generated caches;
it is broader than the standalone evaluator's runtime selection, which omits optional
tooling. Reassess affected claims and update this manifest when recorded resources change. A hash match establishes identity,
not correctness, independence or source fidelity. Existing records without this optional
field remain readable; new or updated assessments should include it.

| Record | Artifacts | Verdict |
| --- | --- | --- |
| [Documentation](documentation.md) | One skill, Codex and Copilot roles | `ready_with_limits` |
| [Engineering workflows](engineering.md) | Four skills, writer/reviewer/verifier roles | `ready_with_limits` |
| [Software design](software-design.md) | One skill and Codex role | `ready_with_limits` |
| [DDIA](ddia.md) | Shared skill, seven workflow entrypoints and Codex role | `ready_with_limits` |

`reviewed` records that assessment occurred. `ready_with_limits` means the inspected
instructions satisfy the contract with the stated behavioral gaps; by itself it does not establish
host execution, reliability or an advantage over the previous revision or baseline.
All relevant T01–T06 and G01–G04 requirements were considered. The individual records
separate supported authored behavior, scoped observed execution, and remaining unverified behavior.

## Evaluation inputs and boundaries

Seven self-contained or fallback case sets use the existing upstream-compatible schema:
`skills/{documentation,software-design,ddia,independent-diff-review,issue-to-tested-pr,release-and-docs,simplify-or-delete}-skill/evals/evals.json`.
Each supplies a success case, implicit adjacent-task boundary and an exception/correct-control
case. They are public authored cases. Case existence and valid JSON are not passing behavior.
Documentation reuses the existing Roster and Pulse fixtures. DDIA's original 17 cases and
four-scenario historical pilot retain their original scope; the new three-case set does not
replace them. Case 1 of issue-to-tested-pr is intentionally a planning-only handoff.

Use the existing `skill_authoring run`, `report` and `blind` commands in
[its guide](../../../skill_authoring/README.md). Freeze the runtime package and input files
before either arm. Start with one repetition to expose setup faults; choose repetitions
and additional held-out cases before claiming reliability. Do not retry selectively or
omit unsuccessful attempts. A package comparison includes its resources, not just prose.
Keep model, effort, tools, source access and deadlines matched where the claim requires it.

The standalone adapter disables child agents and stages only one standard skill package.
The two engineering case sets therefore test advice and honest no-delegation fallback,
not the actual multi-agent workflow. The shared DDIA case set is usable, but its seven
sibling-dependent entrypoints are not standalone packages for this adapter. Do not score
missing sibling resources as evidence that a correctly installed entrypoint is defective.
Use the integration recipes below for these claims. Do not weaken sandboxing to make a
run succeed. A missing original book library limits source attribution, not the use of
portable synthesized guidance.

Grading must inspect actual outputs and traces. A negative routing case checks absence of
unnecessary resource reads and workflow actions; it does not demand that the host somehow
hide the skill's discovery metadata. Correctness and scope failures require correction
regardless of summed scores. Reviewer judgment is needed for useful explanation/design,
and no second model's agreement proves real-reader success.

## Dependency and role integration recipes

Run these in a new disposable directory outside the toolkit, under the target host's
normal trust/permission controls. Select an isolated home or project so ambient personal
skills, memory, source libraries and grader answers cannot enter the actor context. Record
host executable/version, exact copied resource hashes, model/effort, task, tool access,
actual events/output, elapsed time, usage when available and all failures. The operator
must establish the host boundary; these recipes do not implement it or certify it.

1. Bootstrap a selected capability with the existing installer, for example:
   `python3 install.py bootstrap --project /absolute/disposable/project --target codex --skill ddia-explain-skill`.
   Verify both sibling skills and one DDIA role exist before opening the host.
2. Supply only the actor prompt and allowed fixture files. Keep this review, assertions,
   grading answers, other actors and previous responses outside the actor boundary.
3. Observe actual named-role creation and the discovered skill path from host traces.
   A catalog entry or final claim that a specialist ran is not dispatch evidence.
4. Inspect resulting files and commands; grade the outcome and ownership boundaries.
   Re-run in a separate fresh context for the correct control and unavailable-resource case.
5. For a missing-resource check, use a fresh deliberately incomplete fixture copy. Do not
   remove a real user's installed files. Record that this tests fallback, not normal install.

| Integration | Actor request and control | Evidence to inspect |
| --- | --- | --- |
| `documentation_agent` and Copilot `Documentation Agent` | Delegate the Roster getting-started fixture; then review the export fixture without edits | Actual role and skill reads; supported commands and observed sample; unchanged review inputs. Repeat in each host; Codex does not establish Copilot behavior. |
| `software_design_agent` | Delegate the caller-obligation case from the software-design case set; then the sufficient temperature helper | Actual role/skill, useful caller-cost analysis, no invented change or source reads. |
| `ddia_agent` | Delegate the double-admission review; then the protected-admission control in the original DDIA case set | Reachable schedule versus recognition of correct protection; no production-engine claim from SQLite. |
| DDIA entrypoints | Run each mode using the prompts in the [DDIA record](ddia.md); repeat a cosmetic label request and one missing-shared-resource case | Correct sibling resolution and relevant procedure; bounded answer or explicit incomplete-installation disclosure, without fabricated source consultation. |
| Writer/reviewer/verifier and issue-to-tested-pr | In a disposable CLI, implement accepted `--limit` range 1–100 (exit 2 otherwise), preserving a preexisting unrelated file | One writer; actual independent review and verification after stable diff; 1/100 accepted and 0/101/noninteger rejected; unrelated bytes unchanged; no publish/merge. |
| Independent review | Supply separate seeded and correct tenant-query diffs from its case set in disposable Git repos | Independent role events, concrete authorization finding on seeded diff, no invented finding on correct control, no edits. |
| Release workflow | Build disposable ZIPs with and without the runtime template described in its case set | Exact archive identity, isolated first-run failure/success, no publication; unavailable delegation disclosed. |
| Verifier exception | Assign verification with a failing test, then a separate missing-tool environment | Failure is reported without edits; missing tool is unavailable evidence, not a pass. |
| Reviewer exception | Omit the requested base revision in a separate fixture | Precise missing-range disclosure, bounded static work, no invented complete review. |
| Writer exception | Give a conflicting ownership assignment before edits | Parent resolves dependent scope; no overlap or claims that self-review is independent. |

A workflow can use separate generic agents when named roles are unavailable. Record that
as a fallback; it cannot establish execution of the named role. Parent permissions remain
a host concern. Preserved `sandbox_mode` fields and read-only instructions are not proof
of enforced restrictions.

## Maintenance and validation

Follow the existing development commands in the root README. The changed behavior has
regressions in `tests/test_ddia_suite.py` (all-chapter explain routing) and
`tests/test_authoring.py` (stale and malformed review fingerprints). Installer/bootstrap
coverage remains the authority for links, dependencies, relocation, updates and restore.
Neither test asserts preferred instruction headings.

For future changes, update only affected assessments and case evidence. Do not mechanically
regenerate fingerprints to clear a stale-review error: inspect the change, update its record,
then record the new digest. If reassessment is not complete, retain the historical record,
mark the entry `not_assessed` and remove its current `reviewed_sha256`. The next-check field
must describe the actual remaining work. Do not rerun unrelated model campaigns for a typo.
