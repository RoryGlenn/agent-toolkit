# Use Agent Toolkit across your local Codex projects

A personal install makes toolkit skills and named agents available to your Codex
user profile. Global instructions request when to use them; actual session traces
show whether they ran. This guide keeps those checks separate. Named toolkit roles
are Codex-only. Other hosts can use portable skills, and a different `CODEX_HOME`,
user, remote computer, or hosted environment needs its own setup and verification.

## Install from a retained checkout

Use Python 3.11+ on macOS or Linux and keep the toolkit source in a stable location.
Inspect pending work before updating it. The following commands assume you are at
that checkout's root and explicitly select the default personal profile, ignoring
inherited `CODEX_HOME`. For another role directory, supply the same explicit
`--codex-home /absolute/profile` to both installation and status commands.

```bash
git status --short
python3 install.py check
python3 install.py install --target codex --all --home "$HOME" --preserve-legacy-skill doc-agent --dry-run
python3 install.py install --target codex --all --home "$HOME" --preserve-legacy-skill doc-agent
python3 install.py status --target codex --all --home "$HOME" --json
```

The preservation option is useful only when you deliberately retain an independent
legacy `doc-agent`. It leaves that package's existing files unchanged while adding
canonical `documentation-skill` and `documentation_agent`. Repeat the option on
future installs. Omit it if normal alias migration is intended. Conflicting
canonical destinations still cause refusal; inspect them before using
`--backup-existing`, which preserves them in the printed restoration receipt.

Every selected `status` entry should be `current`. That means exact skill symlinks
and regular hardlinked role files point to this checkout. Matching copied bytes,
an installation receipt, or a valid package alone does not establish current links.
Atomic source replacement can detach hardlinks: rerun the preserving install after
updates and check status again. Preserve conflicts with `--backup-existing` when
needed; do not remove foreign files merely to make status pass.

Domain specialists and the implementation owner inherit the caller's model and
effort. Reviewer and verifier roles retain explicit model settings; check them
against your account before relying on the complete workflow. Do not silently
substitute a provider or model after a failure.

## Update the global installation from GitHub

On Linux with user systemd, the optional local updater validates merged public
`main` before refreshing the
retained checkout and its global links. It uses Python and the development tools
already installed in that checkout; it never downloads dependencies or runs a
model. Its scheduled operation is separate from contribution maintenance.

First inspect the checkout and run the development checks. Save a reviewed updater
runtime and daily user units with these commands from the checkout root:

```bash
python3 toolkit_update.py setup --source "$PWD" --home "$HOME" --validation-python "$PWD/.venv/bin/python"
"$HOME/.local/bin/agent-toolkit-update" run
"$HOME/.local/bin/agent-toolkit-update" status
systemd-analyze --user verify "$HOME/.config/systemd/user/agent-toolkit-update.service" "$HOME/.config/systemd/user/agent-toolkit-update.timer"
systemctl --user daemon-reload
systemctl --user enable --now agent-toolkit-update.timer
systemctl --user list-timers agent-toolkit-update.timer
```

Use `agent-toolkit-update` directly if `~/.local/bin` is on your command search path.
Setup saves files without enabling the timer. It preserves recognized earlier setup
files in private backups and refuses unrelated commands or units at those
destinations. Keep the source checkout under your home directory's `repos/` and
inspect the generated units before enabling. The shipped timer checks daily at
**11:30 America/New_York**. The machine must be on; persistence permits a catch-up
activation, not work while powered off.

`status` prints the last recorded result, source path and private evidence directory.
The main outcomes are:

| Result | Meaning and next step |
| --- | --- |
| `current` | Local HEAD equals fetched public main and expected links are current. |
| `updated` | The exact candidate passed deployment checks, source advanced, and links were refreshed and verified. Start a fresh Codex session. |
| `blocked-local-changes` | Tracked or untracked local work is present. Preserve and reconcile it before deployment. The scheduled service treats this expected hold as a successful check. |
| `blocked-history` | Local commits are not an ancestor of public main. Reconcile the histories explicitly. |
| `blocked-installation` | A managed link differs or a new destination collides with personal content. Inspect it; the updater grants no permission to overwrite it. |
| `blocked-layout-change` | An update retires managed entries, or prior entries remain outside a refreshed catalog. Review and reconcile that migration explicitly. |
| `blocked-rolled-back` | Public main is still the revision you rolled back. Review it before an explicit retry. |
| `failed-validation` | A candidate failed a deployment check; inspect `checks.log` and `checks.json` in the evidence directory. Live source remains unchanged. |
| `rolled-back` / `recovered` | A failed or interrupted deployment returned to its prior source revision and verified links. Inspect its transaction before retrying. |
| `recovery-required` | Unexpected edits, an incomplete receipt or another recovery limit stopped automatic rollback. Preserve the transaction and inspect it before further changes. |

Required automated gates are package and authoring checks, installer/routing/project
installation/updater tests, optional usage-audit tests when present, Ruff lint and
format checks, and mypy. The updater also exercises install, status and restore in a
disposable home while preserving a Doc Agent canary. These gates do not execute
model tasks or the benchmark kernel-isolation suites. A missing required tool or
failed gate blocks deployment. The candidate receives an isolated `HOME` and a
minimal environment; its separate checkout is not a security sandbox.

Before promotion, the updater rechecks clean source and exact managed ownership.
It fast-forwards the retained checkout, preserves `doc-agent`, backs up replaced
entries in installation receipts, and requires every selected status entry to be
`current`. It never stashes, commits or publishes local work. A changed role layout
that the installed runtime does not understand blocks deployment until that
runtime is reviewed and refreshed.

Setup requires the existing global installation to be current. It records managed
paths in a private registry retained across runtime refreshes. A removal or rename
requires explicit reconciliation; the updater preserves old entries and reports a
hold. It does not silently leave stale entries while reporting success.

For a retirement hold, `status` lists the affected destinations and, when a
candidate was staged, its `candidate_path`. A remembered-retirement hold can occur
before staging. The private `~/.local/state/agent-toolkit/updates/managed.json`
remembers prior owned paths. An existing dangling symlink counts as present and
keeps the hold active. Deleting the registry or rerunning setup is not reconciliation.
Use a separately reviewed manual migration:

1. Disable the timer with `systemctl --user disable --now agent-toolkit-update.timer`
   and wait for any active update service to finish.
2. Inspect the exact retired paths and candidate changes. Record the current source
   commit, preserve all installation receipts, and back up the retired source
   packages or role files plus their installed entries in a private directory.
   A skill symlink alone does not preserve its package after source retirement.
3. Before changing live source, validate the exact reviewed candidate: require its
   clean SHA to match the fetched revision, run every deployment gate listed above,
   and exercise preserving install/status/restore in a disposable home. Retain the
   results and recheck SHA, index flags and cleanliness afterward. Stop on a failed
   or unavailable gate. The validation example below runs those checks directly.
4. With local work reconciled, recheck the live SHA and clean worktree against your
   recorded pre-migration state, then manually fast-forward to the validated SHA.
   Move only the approved retired global entries into that private backup. This
   explicit migration is outside the updater's automatic overwrite permission.
5. Follow the preserving installation and status commands above for the remaining
   catalog. If the role layout changed, review the new updater/installer and rerun
   setup after the installation is current. Keep `managed.json`: already absent
   retired paths can be reconciled; present remembered paths keep deployment held.
6. Run `agent-toolkit-update run` and inspect `status`. A `current` result after a
   manual source change does not run candidate validation or replace step 3.
   Re-enable the timer only
   after the manual migration is verified, then check a fresh Codex session.

If no `candidate_path` was staged, keep the timer disabled and first inspect the
configured source from `status`. Require the intended repository, branch `main`,
and a clean worktree with no unpublished changes. Fetch the approved public main
into the updater's private ref and create a new detached worktree; these operations
do not advance the live branch. The example assumes the standard retained path:

```bash
toolkit_source="$HOME/repos/agent-toolkit"
toolkit_candidate="$HOME/repos/.agent-toolkit-update-candidates/manual-$(date -u +%Y%m%dT%H%M%SZ)-$$/source"
git -C "$toolkit_source" -c core.hooksPath=/dev/null -c credential.helper= fetch --no-tags \
  https://github.com/RoryGlenn/agent-toolkit.git \
  +refs/heads/main:refs/agent-toolkit-updater/candidate &&
git -C "$toolkit_source" merge-base --is-ancestor HEAD refs/agent-toolkit-updater/candidate &&
git -C "$toolkit_source" -c core.hooksPath=/dev/null worktree add --detach \
  "$toolkit_candidate" refs/agent-toolkit-updater/candidate
```

Stop if fetch, ancestry or worktree creation fails. Review the fetched SHA and its
changes, then use this new `toolkit_candidate` for step 3 below. Retain the worktree
and validation evidence for the migration review.

If an external operation already advanced live source without these checks, treat
that as manual recovery and keep automation disabled. Later validation cannot
establish validation before that earlier promotion. Preserve the current source,
installed entries and receipts; use a separately reviewed recovery plan to restore
the recorded verified baseline before starting this migration sequence. If no
verified baseline is available, remain held until recovery is reviewed rather
than treating `current` as proof that the external change was safe.

For step 3, run the following from the retained checkout after setting
`toolkit_candidate` to the reviewed staged path shown by `status`. Use the existing
development Python configured during setup; the example uses `.venv/bin/python`.
The reviewed candidate supplies its validator so a reviewed layout change can use
its corresponding installer. This command installs only into a disposable home,
writes private check evidence, and never advances live source:

```bash
"$PWD/.venv/bin/python" - "$toolkit_candidate" <<'PY'
import json, sys, uuid
from pathlib import Path
candidate = Path(sys.argv[1]).resolve(strict=True)
sys.path.insert(0, str(candidate))
from toolkit_update import Updater, git, load_settings
cfg = load_settings(Path.home() / ".config/agent-toolkit/update.json")
revision = git(candidate, "rev-parse", "HEAD")
def require(condition):
    if not condition:
        raise SystemExit("Candidate identity or cleanliness check failed; stop migration.")
require(revision == git(cfg.source, "rev-parse", "refs/agent-toolkit-updater/candidate"))
require(not git(candidate, "status", "--porcelain=v1", "--untracked-files=all"))
require(all(line.startswith("H ") for line in git(candidate, "ls-files", "-v").splitlines()))
evidence = cfg.state / "manual-validation" / uuid.uuid4().hex
evidence.mkdir(parents=True, mode=0o700)
checks = Updater(cfg).validate_candidate(candidate, evidence)
require(git(candidate, "rev-parse", "HEAD") == revision)
require(not git(candidate, "status", "--porcelain=v1", "--untracked-files=all"))
require(all(line.startswith("H ") for line in git(candidate, "ls-files", "-v").splitlines()))
(evidence / "validated.json").write_text(json.dumps({"revision": revision, "checks": checks}, indent=2))
print(f"Validated {revision}; evidence: {evidence}")
PY
```

To return the most recent completed update to its prior revision:

```bash
agent-toolkit-update rollback
agent-toolkit-update status
```

Rollback refuses unexpected source or destination changes. It restores the
installation receipt before moving Git back, then relinks the restored source to
repair role inode identity. Its guarded `git reset --keep` applies only to the
recorded transaction; it never uses a hard reset. A subsequent `run` attempts
recovery for an unfinished transaction. A kill during individual installer writes
can leave a pending receipt requiring manual inspection; do not delete it or force
the checkout clean to bypass the hold.

The rolled-back revision remains held on subsequent scheduled runs. A different
upstream revision can proceed through normal validation. To deliberately retry the
same reviewed revision, use `agent-toolkit-update run --retry-rolled-back`.
Recovery also stops if a new installation receipt belongs to another Codex profile.
Both deployment and rollback repair record unique receipt IDs before installation
starts. Recovery restores only those exact matching receipts. Another same-source
installation, even in the same profile, causes a hold before either receipt is
restored; creation time alone never establishes ownership.

The fixed runtime is stored under `~/.local/lib/agent-toolkit-updater/`; configuration
is `~/.config/agent-toolkit/update.json`, and results, transactions, backups and logs
are under `~/.local/state/agent-toolkit/updates/`. Candidate worktrees remain under
`~/repos/.agent-toolkit-update-candidates/` for inspection. Cleanup is a separate
explicit operation. Runtime changes are adopted only by rerunning reviewed setup,
followed by `systemctl --user daemon-reload`; source updates do not silently replace
the running updater. Disable the schedule with
`systemctl --user disable --now agent-toolkit-update.timer`.

Successful linkage and structural TOML validation establish installation state.
Use a fresh Codex session and the execution-evidence procedure below to verify
discovery and real role use; existing conversations can retain earlier definitions.

## Request use through global guidance

Back up your existing `~/.codex/AGENTS.md`, retain its current instructions, and add
a short policy that refers to the installed routing skill. For example:

```md
For substantive tasks, read ~/.agents/skills/task-routing-skill/SKILL.md.
Delegate substantial specialist work to the matching installed named agent.
For nontrivial implementation, use issue-to-tested-pr-skill with one writer and
separate named review and verification agents. Keep the primary agent responsible
for the final result and return assigned subtasks without recursive rerouting.
Keep trivial work direct and honor explicit no-delegation instructions.
Read applicable skills and verify returned work; disclose missing capabilities.
```

The [routing skill](../skills/task-routing-skill/SKILL.md) owns the domain table and
fallback rules. Preserve any established requirement to read the standalone Doc
Agent. Its path and the canonical documentation role serve distinct compatibility
and delegation purposes. Instructions request model behavior; they are not a
mechanical guarantee that every task delegates correctly.

Refresh or start a new local Codex session outside this repository. Test an ordinary
substantial documentation, design, data-correctness, or legacy-code task without
naming the expected agent. Inspect the actual child role, its completed result and
skill access, and the primary's final answer. Test arithmetic and an explicit
no-delegation request as controls. Check CLI, IDE, and desktop independently: a
working CLI or app-server discovery result does not prove the corresponding UI.

## Inspect local execution evidence

The audit uses Python's standard library and makes no network calls. It reads
existing canonical `~/.codex/sessions/**/rollout-*.jsonl` files. It does not run an
agent, copy transcripts, install a hook, or start a recurring job.

```bash
python3 usage_audit.py --max-sessions 100 --since-hours 24
python3 usage_audit.py --trace /absolute/path/to/rollout-example.jsonl
```

Output is JSON with trace hashes, safe session IDs, observed skill accesses,
attempted role calls, parent-linked child starts and completed turns, plus explicit
limits. Prompts, answers, reasoning, commands, credentials, and source-book content
are omitted. The report is printed to stdout; redirect it to a private local file
when needed. Default discovery examines at most 20,000 candidates and selects at
most 100 recent traces; `--max-sessions` supports up to 500. Each file has a
32 MiB inspection limit by default, adjustable with `--max-bytes` up to 128 MiB.

The report keeps a case's `declared_surface` separate from its observed `surface`.
An unmatched surface produces `surface_mismatch`; an unknown recorded surface
cannot verify the requested surface. This prevents CLI evidence from satisfying
an IDE or desktop expectation.

An absent child is not automatically a routing failure: ordinary historical tasks
have unknown eligibility. For declared verification cases, create a local manifest:

```json
{
  "cases": [
    {
      "case_id": "design-review",
      "surface": "cli",
      "session_id": "replace-with-actual-session-id",
      "expected_roles": ["software_design_agent"],
      "expected_skills": ["software-design-skill"],
      "checked_outcome": "not_checked"
    }
  ]
}
```

```bash
python3 usage_audit.py --manifest /absolute/path/to/cases.json --max-sessions 100
```

`checked_outcome` is supplied by the operator after a separate actual check; the
audit cannot grade correctness. Allowed values are `passed`, `failed`, and
`not_checked`. Use `forbid_delegation: true` for a no-delegation control and
`require_no_tools: true` for a trivial control. An unavailable surface uses
`skip_reason: "ui_controls_unavailable"` and `checked_outcome: "not_checked"`.
Skipped checks remain visible and do not establish that surface works.

| Evidence | Meaning and limit |
| --- | --- |
| `current` installation entry | Exact expected linkage at inspection time; not host loading. |
| `skill_reads_observed` | Matching guidance content from a successful recognized read; not proof of application or full comprehension. |
| `role_attempts` | Recorded spawn request; not proof of child execution. |
| Named child start | Native child metadata links it to the parent and role. |
| Completed child | Its own terminal event is observed; not proof of a correct result. |
| Declared routing result | Expected roles compared with observed descendants; eligibility comes from the manifest. |
| Checked outcome | Separate operator-supplied check, not an automatic model-quality grade. |

The parser excludes inherited parent history using Codex's boundary marker. It
reports malformed, conflicting, missing, or truncated evidence instead of treating
it as success. Aborted turns are separate from completed turns. `unclosed_turns`
means no supported terminal event was observed; it is not a live worker-health
check. CLI `--json` stdout streams are a different format: supply canonical
rollouts rather than those streams. Read recognition supports file-read tools and
simple `cat`, `head`, `tail`, and `sed` shell reads, including common code-mode
wrappers; other read methods can remain unobserved. It does not inspect encrypted
reasoning or infer usage from a final self-report.

Exit status is `0` for a fully parsed selection whose declared routing checks have
no observed failure; declared skips can still be present. It is `1` for partial
evidence, a routing/read failure, or a supplied failed outcome, and `2` for invalid
inputs. Always read the per-case fields and limits. Bounded smoke cases and unknown
historical eligibility do not establish universal adoption or comparative benefit.

## Restore a rollout

Keep the installer receipt and a separate backup of the original global guidance.
First inspect then restore the installation recorded by that receipt:

```bash
python3 install.py restore /absolute/path/to/receipt.json --dry-run
python3 install.py restore /absolute/path/to/receipt.json
```

Restore global guidance from its original backup and verify the saved hash. The
installer does not manage global instructions, a preserved standalone skill, or
independent private book libraries. Receipts refuse restoration over changed
destinations and protect surviving shared dependencies; resolve the specific
reported conflict before retrying. A disposable install/status/restore check is
useful recovery evidence, but does not establish a full-machine recovery.
