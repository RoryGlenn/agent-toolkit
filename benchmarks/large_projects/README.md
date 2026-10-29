# Large-project curator handoff

This is the portable starting material for [issue #5](https://github.com/RoryGlenn/agent-toolkit/issues/5),
not a completed benchmark or a model-comparison result. These files contain reference answers.
Keep this directory, its downloaded Git objects and the issue out of candidate environments.
The existing RecordBatch CLI and scoring behavior are unchanged.

- `catalog.json`: four immutable parent/fixed pins, task drafts, exact upstream test paths and
  patch digests. Difficulty is a hypothesis, not a measured outcome.
- `prior-qualification.json`: sanitized account of native macOS arm64 reproduction and its
  independent evidence audit. Original qualification digests identify local records; those
  original records are not bundled, so the digests cannot authenticate this summary by themselves.
- `command-recipes.json`: historical commands and results with machine paths replaced by
  placeholders. They are migration references, not an executable plan or Linux proof.
- `prepare.py`: source preparation only. It fetches a shallow pinned reference, verifies its
  direct parent and canonical test patch digest, and creates `parent` (with upstream tests) and `fixed`
  worktrees. Both share answer-bearing Git objects. It does not install dependencies, compile,
  execute tests, configure isolation, or launch models.
- `cloud-task.md`: the implementation task to give the cloud worker after environment setup.

## Prepare one curator workspace

From the toolkit checkout, with Python 3.11+ and Git on macOS or Linux:

```sh
python3 benchmarks/large_projects/prepare.py otel-queue-cancellation /tmp/collector-curation
```

The destination must not exist. Failure preserves partial downloads for inspection; choose
another empty destination after diagnosing it. Commands have a five-minute timeout and kill
only their task process group. Git hooks and LFS download filters are disabled per command;
no global Git configuration is changed. Diff generation ignores user/system configuration,
uses full blob IDs and fixed formatting, and removes informational hunk function labels.
This keeps catalog digests stable across shallow object sets and diff preferences. Fetch
authentication and transport settings remain available; only diff generation ignores them. LFS pointer retention is acceptable only for assets
proven unrelated to the selected tests. Do not use these worktrees as candidate sandboxes.

The test-only patch is reconstructed from public Git history rather than vendored. Retain each
project's license and attribution when later copying upstream code or tests into the toolkit.
Build one project at a time initially; use two compilation workers and record available disk.
Do not delete unrelated files to make space. Preparation of all four projects can use several
GiB once dependencies and binaries are included.

## Qualification and migration

The prior results establish real historical fail-before/pass-after behavior. They do not
establish fair grading of every alternative implementation, cloud compatibility or candidate
isolation. `prior-qualification.json` records private test hooks, optional-module skips,
mock storage, exact-output constraints and incomplete platform/suite coverage.

Historical commands use `{corpus}` paths from the original workspace layout. Map them to the
new `parent` and `fixed` directories; create private build/install/cache/output directories
outside source as needed. Do not blindly execute recipe strings. Go executable and make paths
are normalized to PATH-resolved names, Node's PATH to `{node_bin}`, and the macOS OpenSSL
prefix to `{openssl_prefix}`. The CPython interpreter may be `./python` on a case-sensitive
Linux filesystem instead of the observed `./python.exe`. Separate builds avoid stale frozen
importlib; any in-place transition must regenerate it and verify the executing interpreter.

For Linux, inspect the pinned project's contribution/build instructions, then validate actual
package availability and required native tools. VS Code needs Node 22.22.1 and npm 10.9.4 plus
headless Chromium dependencies. Collector needs Go 1.26.0 and C tooling for `-race`. CPython
and PostgreSQL need C build tools; PostgreSQL needs suitable Bison/Flex. Preserve reproducible
versions. Do not infer that host browser-control support determines whether CLI Playwright
can launch: test the headless harness explicitly. Repository development checks use `uv`.

No cloud task, environment, Linux build or model comparison was validated by this handoff.
Follow issue #5 for the remaining adapter, grading, runtime-isolation and verification work.
