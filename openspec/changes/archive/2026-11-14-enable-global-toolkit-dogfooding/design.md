# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. The existing personal
installer links skill directories and hardlinks Codex TOML roles, writes reversible
receipts, and deliberately does not edit global guidance. The newer tracked source
adds a linkage-only `status` command. The workstation currently has three toolkit
skills and two roles from a retained legacy-code worktree. Its primary checkout is
33 commits behind its cached upstream, with overlapping untracked OpenSpec files.
The installed standalone Doc Agent differs from the toolkit's documentation skill
and its exact path is explicitly required by the user's global instructions.

Native local roles are a Codex capability, not an operating-system-wide service.
CLI, IDE, and desktop may use different binaries or app-server processes, so shared
files establish common setup but do not establish each user-facing flow. Previous
bounded legacy-code smoke evidence also distinguishes a natural direct skill read
from an explicitly requested named consultation; neither proves universal adoption.

## Goals / Non-Goals

**Goals:** One retained source, complete selected personal installation, explicit
task-appropriate delegation, reversible changes, and conservative local evidence.
Use existing installer/status/routing conventions and standard-library tools.

**Non-Goals:** No new router service, host adapter, scheduled job, blanket delegation
for trivial requests, paid benchmark campaign, security-policy expansion, private
source-book upload, GitHub delivery, or claim that a backend run verifies a UI.

## Decisions

### Keep installation, policy, and evidence separate

Extend `install.py` only for explicit legacy-skill preservation. Keep `status`
strictly about canonical linkage. Put the short global policy in personal
`AGENTS.md`, referring to the existing routing skill rather than copying its domain
table. Put trace inspection in a small on-demand command with no host mutations.
An all-in-one daemon would add lifecycle and privacy obligations without solving a
need in this request.

### Preserve the established Doc Agent without changing its identity

Add repeatable `--preserve-legacy-skill` selections to personal install only. Accept
recognized legacy aliases; omit their retirement candidates while preserving
canonical destination collision handling. Record the selection in new receipts;
old receipts remain valid. The two packages intentionally retain distinct names.
A symlink replacing the old directory would keep the path but silently replace
the user's existing workflow; ad hoc movement would make future installs and
restore instructions unreliable. Default migrations remain unchanged.

### Refresh source with a verified preservation boundary

Before update, hash and copy global guidance, selected host entries, receipts,
preexisting untracked project files, and preexisting dotfiles changes into private
state. Fetch upstream and require a fast-forward. Move only untracked paths that
would obstruct the update into that snapshot, then restore differing local bytes
as explicit pending work and verify hashes. Keep the old worktree and private book
libraries intact. A clean new download would needlessly duplicate the source and
leave the primary checkout stale.

### Respect the user's model configuration

Inventory role overrides before invoking them. Existing domain specialists inherit
the parent. The imported engineering roles pin older models. A cache entry is only
discovery evidence: actually test required pinned paths. Preserve a failed attempt
and, if a pin is unavailable, make the smallest assessed correction to inherited
parent configuration rather than silently selecting an arbitrary replacement.
Update affected authoring review/fingerprint records if any role bytes change.

### Make substantive delegation explicit and bounded

The global rule requests matching named agents for substantial documentation,
design, data, and legacy-code work and the existing one-writer/reviewer/verifier
workflow for nontrivial implementation. The primary agent remains responsible.
Trivial requests remain direct; explicit no-delegation and assigned-subtask scope
win. Avoid recursive specialist dispatch or a mandatory multi-agent panel.

### Audit actual trace events, not prose claims

Read canonical local session JSONL. Recognize metadata, tool calls/results, linked
named-child starts, and own-task completion. Use call IDs and child-parent linkage;
do not count copied parent history as child activity. Bound discovery by count and
time, stream each selected file, and identify inspected bytes by SHA-256. Unknown
or malformed formats remain explicit. Tool-read evidence can identify a skill
without copying its output into the report.

An optional local verification manifest supplies case IDs, exact session identity,
expected role/skill, whether direct use is allowed, surface, and independently
checked outcome. It supplies eligibility, not execution proof. Ordinary sessions
without expectations have unknown eligibility. The report distinguishes attempted
calls, started/completed named roles, skill-read evidence, checked results, skips,
and gaps; it never manufactures an adoption rate from unknown tasks.

### Verify actual surfaces before making surface claims

Use synthetic fixtures outside the toolkit and fresh ordinary sessions with no
agent names in the natural prompts. Test docs, design, data guarantees, legacy
test seams, a bounded implementation, explicit no-delegation, and arithmetic.
Observe named execution and primary synthesis; independently verify the fixture
result. Inspect available desktop/IDE controls and existing supported app-server
interfaces. Preserve open apps/profiles and do not expose debug ports, copy access
identities, or restart unrelated apps. A missing UI route remains a precise limit
while backend discovery and other working flows continue.

### Keep recovery and evidence local

Store private snapshots, trace manifests, full test logs, and sanitized results in
`~/.local/state/agent-toolkit/dogfooding/<run>/` with private directory permissions.
Do not add credentials or transcripts to Git. Save only portable global guidance,
setup commands, and restore instructions in the existing private dotfiles repo;
preserve its pending unrelated changes. Use explicit receipts in rollback and
verify a disposable restore before describing recovery as checked.

## Risks / Trade-offs

- Instructions influence model behavior rather than guaranteeing every invocation
  → combine explicit policy, natural prompts, event-based checks, and visible gaps.
- Hardlinks can detach when Git replaces source files → rerun selected preserving
  install and linkage status after updates; never infer status from matching bytes.
- Existing local OpenSpec differs from upstream → keep both original snapshot and
  restored pending bytes; report them separately from this change.
- Two documentation skill names remain installed → explain their deliberate
  compatibility purpose; use the canonical named agent for substantial work.
- Trace envelopes evolve and histories repeat → parse supported structural events,
  deduplicate identity, and report incomplete evidence instead of false passes.
- Native sandbox/UI access may be unavailable → test only authorized synthetic
  scope, disclose boundaries, and do not relabel isolated or backend runs as UI proof.

## Migration Plan

1. Validate this plan and inventory/snapshot current state.
2. Fast-forward the retained primary checkout, preserving local differences.
3. Implement and test legacy preservation and local trace audit; independently
   review the first complete diff before final acceptance.
4. Dry-run and apply the full personal install with explicit Doc Agent preservation;
   read back all canonical links/roles and the compatibility package fingerprint.
5. Back up and update global guidance, mirror portable policy and restore guidance
   in dotfiles, and verify them in a disposable target home.
6. Execute bounded natural and control cases on available real surfaces; retain
   failures, actual model settings, trace identities, outcomes, and exact limits.
7. Run the local audit, required repository checks, independent review/verification,
   final readback and diff inspection. Reconcile tasks and progress with evidence.

Rollback uses the new installer receipt before restoring earlier receipt-backed
entries, restores the original global guidance snapshot, and verifies its hashes.
Private source libraries and retained old worktrees are independent and untouched.
