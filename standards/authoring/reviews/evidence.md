# Adoption execution evidence

Source baseline: `156ca63e5bbc1a76205c24d919a3d9b4d3c13d36`.
Environment: macOS arm64, Python 3.13.12. This record separates executed checks from
available fixtures and proposed integrations. The review records are source assessments;
they do not claim independent execution or agent superiority.

## Baseline checks observed

The implementation agent ran `uv sync --frozen --group dev` successfully, then
`uv run python -m unittest discover -s tests -v`: **187 tests passed**, 25.959 seconds.
These are repository mechanics and trusted controls, not a new model evaluation.

## Migration checks observed

The implementation agent ran these on the migration worktree after the source changes:

| Command | Observed result |
| --- | --- |
| `uv run python -m unittest discover -s tests -p test_ddia_suite.py -v` | 12 passed, including all-chapter explain routing |
| `uv run python -m unittest discover -s tests -p test_authoring.py -v` | 17 passed, including changed/malformed review identities |
| `uv run python -m unittest discover -s tests -v` | 190 passed, 27.040 seconds |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed, 34 files |
| `uv run mypy` | Passed, 22 source files |
| `uv run python authoring.py check` | Valid, 21 inventoried artifacts; behavioral assessment not performed |
| `uv run python -m skill_authoring verify-upstream` | All pinned files verified |
| `python3 install.py check` | 14 skills, six Codex roles, one Copilot role valid |
| `uv run python -m benchmarks validate` | All 12 reference/wrong controls plus the design sequel passed |
| `git diff --check` | Passed |

Also parsed each of the seven `skills/*/evals/evals.json` through
`skill_authoring.workflow.cases`: all 21 case definitions and their referenced input files
were accepted. This check executes no models. Runtime manifest hashes were checked against
all recorded files. Existing full-suite installation/bootstrap tests cover dependency
closure, selected/full installation, restore, relocation and conflict refusal.

## Independent review and verification

A separate source reviewer inspected the requirement, diff, assessment records and evidence
boundaries. The reviewer and independent verifier identified inaccurate wording about the
resource manifest: it includes optional documentation tooling, whereas standalone evaluator
staging does not. The README and grouped records were corrected. The source reviewer also
reviewed the later documentation/Copilot corrections and reported no material source findings.
This is independent source review, not external certification or exhaustive behavioral testing.

The independent verifier repeated the final source gates: **190 tests passed**, 26.352 seconds,
including separate 17-test authoring and 12-test DDIA runs. Lint, format, strict typing,
package, upstream, authoring and diff checks passed. The benchmark validated all **13 phases**
(12 cases plus the design sequel). An earlier independent full run passed in 28.430 seconds;
that earlier result is not substituted for the final-source run.

A fresh regular-file source snapshot passed **24 actual CLI operations** covering full
both-host install/no-op/dry-run/restore, DDIA sibling dependencies and one role, legacy-selector
conflict/backup/restore, source-archive provenance, bootstrap, relocation/update/dry-run,
local-edit and unmanaged-collision refusal, and unrelated-file/instruction preservation.
All seven evaluation sets (21 cases) parsed. Final verification matched all **79** recorded
resource/role hashes. `install.py` and `project_bootstrap.py` remain byte-identical to the
baseline; all six Codex roles retain their non-instruction fields. The native skill validator
accepted all 14 skills before the last documentation example; the changed documentation
skill was revalidated afterward. Native metadata validation is not evidence of live behavior.

## Retained live evidence

[observations.json](observations.json) contains sanitized settings, frozen resource hashes,
attempt outcomes, independent grades and output/trace identities. Raw traces, credentials,
private session identifiers and full model reasoning are excluded. Hashes identify retained
local artifacts; publishing a digest alone does not let another reader inspect its contents.
The receipt supports the observations below with scoped grader evidence and explicit limits.

The existing standalone evaluator ran **20 actor sessions** across four paired campaigns.
Every campaign used `gpt-6-astra`, high effort, one repetition and a 180-second per-session
deadline. All sessions completed; all native canaries passed before temporary credential
staging, and staged credentials were removed. A separate reviewer graded the outputs and
traces across the campaigns. Existing report generation completed for every campaign; documentation also produced
a blind-comparison bundle. The runs compare package present/absent, not old/new prose alone.

| Campaign | Runtime and cases | With / without skill |
| --- | --- | --- |
| `docs-before` | Earlier documentation runtime; Roster first success, translation boundary, Pulse reference; six sessions | 8/8 expectations in each arm |
| `release-and-docs-skill-after` | Current release skill; omitted runtime template, spelling boundary, ambiguous publication; six sessions | 8/8 in each arm |
| `simplify-or-delete-skill-after` | Current simplification skill; redundant wrapper, sorting boundary, required replay identity; six sessions | 8/8 in each arm |
| `pulse-final` | Final documentation runtime (`SKILL.md` SHA-256 `54a2cfc4ac454196ff98bdae700bc8b6d44d8066e387c8bdc1b55b19bbcca52a`); Pulse reference; two sessions | 3/3 in each arm |

The initial documentation campaign preceded the final schema-precision example. Its Roster
and translation results cannot be described as final-runtime evidence; those cases remain
available for a later targeted repeat. Pulse was rerun against the final runtime and its
unchanged source fixture. All arms tied on scored outcomes. These small public cases establish
no general reliability, statistical advantage, real-reader success or toolkit superiority.
Release and simplification cases test advice and boundaries; they do not constitute actual
registry publication or production component removal.

Per-session timing and observed root-token usage are retained in the receipt. For example,
`docs-before` averaged 53.9 seconds/71,525 tokens with skill versus 49.6 seconds/48,141 without.
One repetition is not a stable cost estimate or speed advantage. Root usage must not be
presented as aggregate descendant usage in the separate multi-agent integration below.

## Native Codex role integration

The first role attempt exhausted its requested shared 40,000-token budget after dispatching
DDIA and software-design roles. Its external controller check also hit a sandbox denial for
an unresolved virtual-environment interpreter path. Both failures are retained. A new attempt
used a 300,000-token requested weighted budget, a 600-second deadline and the resolved
interpreter path; it completed in 250.184 seconds and passed external contract controls.
The two attempts changed execution settings and are not a matched effectiveness comparison.

A separate verifier inspected run-local sessions and task artifacts, confirming all six
named Codex roles actually ran. DDIA, software-design and documentation roles read their
skills; consultants disclosed absent original book libraries. One implementation owner
changed the integer-inventory fixture and demonstrated regression failure before the fix
and five passing tests afterward. Distinct reviewer and verifier ran after writer completion
without source edits. The original contract remained unchanged. The documentation role then
added only README.md and executed its example. No role recursively spawned itself.

This run normalized roles to `gpt-6-astra`/high; it does not test shipped personal model
overrides. Reviewer and verifier inherited parent history, so they are separate actors but
not blinded or given clean requirement-only contexts. The later README was example-tested
by the documentation role and inspected by the independent assessor, not by the earlier
code reviewer/verifier. The documentation skill's final schema-precision example was added
after this role run; actual final-runtime documentation behavior is limited to the final
Pulse and Copilot observations. Missing-source fallback does not establish source retrieval.

Root reported usage was 428,598 input tokens (386,944 cached) and 3,533 output tokens.
Aggregate descendant usage remains unknown; requested weighted budget is not equivalent
to raw root tokens, and this assessment does not establish strict aggregate budget enforcement.
One controller-created `__pycache__` after the actor's listing was a verification artifact,
not an observed actor scope violation. No production or large-repository claim follows.

## Copilot observed failures, corrections and final checks

Pinned Copilot CLI `1.0.89-4` first demonstrated skill/project-instruction discovery. Its
initial role-execution attempt lacked authentication. Later bounded attempts used an existing
compatible GitHub CLI OAuth credential transiently in a secret-marked environment variable;
no account settings or persistent credential configuration were changed. The initial run used
host-default `claude-sonnet-5` at medium effort; subsequent repeats explicitly pinned those
same observed settings. All used restricted read-only task tools.

The retained development sequence exposed four failed behavioral attempts:

1. Actual role selection, but directory listings instead of loading the skill, followed by
   unsupported API claims. The wrapper was clarified to require an actual file read.
2. Actual skill loading, followed by substitution of its fictional export-review evaluation
   fixtures for the supplied jobs scenario. The wrapper distinguished methods from task inputs.
3. Correct skill/task selection, but invented response-field and processing-start semantics.
   A general output evidence checkpoint was added.
4. The same unsupported field/state inference persisted. A different DELETE scenario passed,
   but that did not erase the failure. One compact schema-precision counterexample was added
   to the shared skill instead of further repeating wrapper instructions.

A separate verifier then inspected the **two final-runtime cases**: the original sparse
jobs scenario and the different DELETE scenario. Both passed with actual persisted role
selection, one successful SKILL.md read, no evaluation-fixture reads, no unsupported API
fields/state/mechanism claims, and no edits. Project-managed files and instructions were
preserved. The prior four failures and earlier DELETE pass remain in the receipt.

The original prompt was reused during revisions; its final pass is development evidence,
not held-out validation. The different DELETE case was also repeated on final runtime and
does not establish broad transfer. These results support two observed final-role behaviors,
not guaranteed instruction following, general reliability or an advantage over another host.

## Remaining evidence limits

The package/format migration and scoped observations are complete. Broader reliability,
normal implicit routing for every role/entrypoint, all seven DDIA workflow integrations,
additional failure paths, shipped personal model combinations, successful private-source
retrieval, browser accessibility and real-user outcomes remain unverified. The advice-only
workflow campaigns do not replace a full delegated workflow comparison. Future checks should
use fresh cases and preserve these failures rather than relabeling them as passes. No new
scheduled evaluation, external publication or global installation was performed.
