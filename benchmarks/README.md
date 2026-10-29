# Public development benchmark

This is a runnable, twelve-task development benchmark for the toolkit's three book-based
specialists and integrated workflow. It measures objective task behavior separately from
independent design/documentation review. The cases are public, small and deliberately
constructed. Difficulty labels are provisional. This is not a private held-out benchmark,
a production-quality claim, or evidence that the toolkit improves outcomes before results
are collected.

Run from the repository root with the existing development environment:

```bash
uv sync --group dev
uv run python -m benchmarks list
uv run python -m benchmarks show ddia-hard
uv run python -m benchmarks validate
```

`validate` runs all trusted reference solutions and targeted wrong controls, including the
second design-hard phase. Each reference must satisfy its executable oracle and each wrong
control must fail it. This command deliberately uses ordinary bounded subprocesses **only
for repository-owned controls**. It does not execute submissions and does not establish
native isolation. CI runs this deterministic check without credentials or model calls.

## Cases and evidence

`cases.py` is the versioned manifest and complete actor task source. `list` emits its JSON
manifest, including hashes of the task, fixture and oracle; `show` emits one complete task.
`recordbatch/` contains the original Python/SQLite/JSON CLI and zipapp builder. `oracles.py`
is trusted curator code, never copied into actor projects.

| Family | Easy | Medium | Hard |
| --- | --- | --- | --- |
| DDIA | Tenant/request identity | Atomic capacity admission | Crash/replay/ack/cleanup effect identity |
| Software design | Absent deletion and honest errors | Arbitrary-iterable batch API | Output boundary, then fresh-maintainer sequel |
| Documentation | Checked newcomer quickstart | Asynchronous contract examples | Archive-only recovery and seeded DB upgrade |
| Integrated | Tenant-scoped status filter | Cancellation/resumption race and package | External-delivery uncertainty and reconciliation |

The application contract is limited to SQLite transactions and process restart. True
process exits exercise before-commit, after-commit-before-ack, and external-call crash seams.
Parallel subprocesses use independent connections. Tests do not impose internal barriers
that would deadlock a correct locking implementation. Acknowledged messages deliberately
replay after cleanup. External delivery tests use two identical observable timeout errors
with different effects; both must remain unknown, never become false success or blind retry.

Wrong controls are substantive defects: cross-tenant identity collision, leaked capacity
on failed insertion, discarded durable effect identity, absence treated as an error,
list-only batch iteration, missing output adapter, incorrect documented outcomes, ignored
status filtering, repeated capacity release, and timeout mislabeled as delivery. Functional
oracles accept alternative implementations that satisfy the public file/API/CLI contracts.
No keyword, line-count, class-count, or agent-reported “passed” claim supplies a score.

A successful objective run is `passed` only when no human-assessed dimension remains.
Documentation clarity, factual completeness outside executable examples, design quality,
and fresh-reader/maintainer judgment remain `needs_review`. An independent reviewer must
inspect the frozen artifact against the review questions in the manifest and record who
reviewed what, the artifact fingerprint, evidence, and any unresolved issues. The runner
never upgrades those dimensions based on fluent model prose. Executable examples are not
real-user evidence.

## Plan and run a comparison

Native execution currently targets Codex CLI 0.165's permission profiles on macOS or Linux.
It requires an existing signed-in Codex CLI and a regular `auth.json` explicitly selected
by the operator. It does not create keys, change global settings, or install live skills.
Before a paid run, choose the model available to that account and a bounded wall duration:

```bash
uv run python -m benchmarks plan \
  --case design-easy --model MODEL --effort high \
  --seconds 300 --attempts 1 --budget-units 20000 \
  --output .benchmark-runs/pilot-plan.json
uv run python -m benchmarks run .benchmark-runs/pilot-plan.json \
  --auth-source /absolute/path/to/selected/codex/auth.json \
  --output .benchmark-runs/pilot
uv run python -m benchmarks report .benchmark-runs/pilot \
  --output .benchmark-runs/pilot/report.json
```

Omitting `--case` plans all twelve cases. Repeat it to select a subset. All three arms are
included unless selected with repeated `--arm`. The plan fixes task versions, model,
reasoning effort, source profile, wall deadline, optional weighted budget, and attempt cap.
Each plan also binds the exact Python harness/runtime sources. Changing the runner invalidates
a saved plan; its new results form a separate report group. Legacy records without this
fingerprint remain unrecorded and are separated by plan rather than assigned today's runtime.
Arm order rotates deterministically within each paired task/repetition. There are at most
four attempts per arm/task, and there is no automatic retry or best-of-many selection.
Every attempted setup failure, timeout, unsuccessful completion and `needs_review` result
is retained. A new plan is needed when task or source fingerprints change.

`prepare PLAN --index 0 --output NEW_DIRECTORY` stages an inspectable attempt without
running a model. `grade ARTIFACT --case design-easy --output NEW_DIRECTORY` grades a
submission with native isolation; it has no unsandboxed-submission option. Grade uses the
same command/network boundary as the actor and never imports candidate Python into the
trusted grader. The Python executable and runtime directory are explicitly readable.
A candidate's API client executes in its own sandboxed Python process; trusted code compares
returned data and persistent SQLite state outside that process.

The `run` command saves the complete schedule and its checksum before execution, then
writes one `result.json` per planned attempt with its run/plan IDs,
configuration, source/toolkit/task fingerprints, exact commands, statuses, final response,
JSONL trace, objective checks and artifact hashes. `artifact/` is frozen before grading;
`grading/` is a separate execution copy. Reports verify result/evidence checksums, frozen
artifact hashes, and objective completion structure against the saved schedule; absent
results remain `not_started`. Hashes detect evidence changes, not a malicious operator who
can rewrite both evidence and checksums. Authentication is copied directly to the protected
client home for the invocation and removed in `finally`; credential contents are never
printed, fingerprinted, added to prompts, or intentionally included in result records.
Keep run directories private: they may contain explicitly staged private books and traces.
The default documented `.benchmark-runs/` location is ignored by Git. Removing a run directory
is an operator action after evidence is retained where desired.

## Arms, sources and model fairness

- **baseline:** stock generic Codex capabilities, no toolkit instructions or book resources.
- **source-matched:** the same original books, retrieval scripts and reference/assets files
  staged for the toolkit arm, with no skill entrypoints or custom role instructions.
- **toolkit:** copies of all nine real toolkit skills and the six
  shipped Codex roles, with evaluation directories excluded. Routing is natural; the prompt
  does not prescribe a specialist. Copies are ordinary independent files, not links into
  the repository or personal installation.

The benchmark stages the validated canonical inventory into an isolated **user layout**
(`actor-home/.agents/skills` and `client-home/agents`). It does not run project bootstrap or
compare bootstrap layouts. Skill/role names follow the repository naming authority: for
example `ddia-skill` / `ddia_agent`, `software-design-skill` / `software_design_agent`, and
`documentation-skill` / `documentation_agent`. Optional source libraries remain distinct:
`ddia-skill` reads `.local/share/ddia-specialist`, and `software-design-skill` reads
`.local/share/software-design-specialist`, matching the retrieval helpers' defaults.

`--profile downloaded` uses only repository books and resource files. It explicitly reports
missing software-design source/index and DDIA extracted-index/private-study material.
It never falls back to the user's existing library. `--profile reference-complete` requires
an explicit JSON source manifest with exact SHA-256 hashes. For both DDIA and software
design, source.epub and its matching index.json must be supplied. Optional personal reading
notes/chapter syntheses can also be explicitly listed; private evaluation/rubric artifacts
and executable instruction entrypoints are rejected. Completeness means the declared
original-source retrieval set, not an assertion that every private study was supplied or
that the model read it.

```json
{
  "version": 1,
  "files": [
    {
      "source": "/explicit/library/ddia/source.epub",
      "target": ".local/share/ddia-specialist/source.epub",
      "sha256": "ACTUAL_SHA256"
    }
  ]
}
```

The abbreviated example is deliberately incomplete: provide source.epub and index.json
for **both** specialists, with hashes from those actual regular files. Pass it using
`--source-manifest /path/to/manifest.json`. No broad credential/library discovery occurs.
Source data cannot authorize commands or override the task. Source-matched and toolkit
arms receive byte-identical resource files. The source fingerprint also identifies the
resource set deliberately withheld from baseline.

The default `--mode controlled` rewrites staged role model/effort selections to the declared
parent values and records the original toolkit fingerprints. Generic children have the same
defaults. The separate `--mode shipped` preserves shipped role model selections and is never
pooled with controlled runs. Legacy role sandbox fields are removed in both modes so parent
permissions remain authoritative. The actor cannot write parent roles, skills or config.
A discovered role/skill is not evidence it ran. Reports record explicit spawn events and successful source-access commands when exposed.
If stdout omits dispatch, the runner inspects only this run's `client-home/sessions` headers,
binding `source.subagent.thread_spawn.parent_thread_id` descendants to stdout's root thread.
It records actual `agent_role` values, not catalog entries. It extracts model/effort only from
the child's own turn context after its inherited-history boundary; unavailable fields remain
null. It never searches global sessions or copies profile/identity/instruction fields into
these diagnostics. Unreadable or incomplete metadata is disclosed. Source-access command completion is not proof of understanding or reading.

One external wall deadline bounds the parent process group and its ordinary children.
The optional native `features.rollout_budget` requests a shared weighted budget across
the root/child session tree. Its source-defined accounting uses provider units when present,
otherwise output plus non-cached input with the configured weights. Native enforcement is
**requested but unverified** until an exhaustion control succeeds on the exact runtime.
The source-defined completion boundary permits overshoot; parsing configuration is not
evidence that a live run stops. Root usage is recorded if emitted; aggregate
child tokens, weighted usage/overshoot and cost remain null when not observable. Null never
means zero. Do not claim exact equal compute, tokens or dollars from a common declared cap.

## Isolation and limits

Each attempt has independent actor HOME, CODEX_HOME, workspace and private temp directories.
Only the workspace/temp are writable; staged resources are read-only. The native profile
denies root reads and network, with minimal system/Python/Codex executable exceptions.
Legacy `--sandbox` and `sandbox_mode` are omitted because they override these profiles.
Tools that could bypass command networking are disabled: web, apps/connectors, plugins,
MCP configuration, browsers/computer use, memory, hooks and permission escalation. Bundled
skills and automatic project instruction loading are disabled; the task is supplied directly.
Tasks receive a plain source snapshot without Git metadata or history. The isolated PATH
exposes canonical Git (on macOS, the real binary selected by host `xcrun`, bypassing the
`/usr/bin/git` shim), with narrow read grants for that binary and its git-core helpers.
Preflight exercises `git --version` and a real no-index file diff. System/global Git
configuration and credential prompting are disabled. Repository discovery stops at the
workspace boundary, including when runs are nested inside the toolkit checkout. The selected
Git paths/version are
recorded with each preparation.

The child shell receives an explicit PATH/HOME/TMPDIR/locale/Python/Git environment and
cannot request a login shell. This does not modify the operator's environment.

The explicitly selected auth is provisioned before actual tool/catalog inspection;
unauthenticated prompt inspection may omit tool definitions and cannot pass. Native
preflight proves interpreter startup, allowed workspace reads/writes, denied reads
of controller/source-repository/client/personal config files, denied symlink alias access,
denied outside writes, and denied connection to a live loopback listener. Missing files or
a failed interpreter launch cannot count as network denial. The actual initial prompt and
discovered catalog are captured and checked for host contamination before execution.
If native restrictions or prompt inspection cannot be established, the attempt is a
`setup_error`; there is no fallback to an unsealed agent. Live model/auth traffic is the
Codex client's separate transport, not actor command network permission.

Archive consumers are staged outside every previously candidate-writable directory and
receive a separately verified sandbox. Controller reads use no-follow descriptors, and
SQLite state is inspected in an isolated subprocess with a five-second external deadline,
a progress/instruction limit and bounded output. The fresh snapshot includes committed WAL
frames; the privileged grader never executes candidate database SQL. No controller writes target a
candidate-created consumer path. The grader rejects symlinks, configuration artifacts,
nonregular files, oversized trees,
unsafe ZIP entries and archive decompression bombs. This is a local development isolation
boundary on the supported CLI/OS, not a claim of defense against kernel vulnerabilities or
hostile descendants that evade normal POSIX process-group cleanup. Do not use this runner
as a general adversarial code hosting service. Native Linux behavior must pass its own
canaries on the intended host; passing deterministic CI does not establish it.

## Fresh-maintainer sequel

The design-hard first artifact is frozen before a separate fresh process/session receives
the second task. Its second adapter consumes a nested representation and arbitrary iterables.
Plan phase 2 from an actual phase-1 `result.json`:

```bash
uv run python -m benchmarks plan --case design-hard --phase 2 \
  --parent-result /path/to/phase-1/result.json --model MODEL --effort high \
  --seconds 300 --output .benchmark-runs/sequel-plan.json
```

The parent artifact hashes are verified, copied into a fresh attempt, and the sequel task
is supplied only then. Phase 1/2 and differing parent artifacts are separate evidence, never
one pooled task score. No live maintainer execution or structural judgment is claimed by
the deterministic phase-2 reference control.

## Reports and calibration

Reports keep separate groups for task/version/phase, sources/profile, toolkit package,
model/effort/mode and budget. Pairing requires the same predeclared plan and repetition.
Inconclusive setup/timeouts remain visible. A pair is complete only when every planned arm
reaches a terminal outcome; not-started or interrupted setup rows keep it incomplete. Tables and
JSON show every attempt, objective outcome and outstanding review dimension. Repetitions do
not increase the distinct-task count. There is no dashboard or single “toolkit intelligence”
score. Use a bounded pilot to inspect model/tool compatibility, native routing/source
observability, task validity and failure rates before a larger run. Preserve failed attempts
when changing the next plan, and label results exploratory until difficulty and independent
review have been calibrated.
