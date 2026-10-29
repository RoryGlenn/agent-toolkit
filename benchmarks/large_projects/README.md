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

The original handoff did not validate a cloud environment or Linux build. The Linux sections
below and the [current verification record](verification/README.md) describe the adapter work
completed since then. No model comparison has been run; issue #5 remains open.

## Linux curator execution

The `large` namespace of the existing benchmark CLI now provides **model-free curator
operations**. It reuses the common bounded subprocess runner. It does not add these cases
to model planning or grading, provision credentials, or launch a comparison. Issue #5
remains open until the outstanding qualification and candidate-runner requirements below
are satisfied.

Prerequisites: Linux x86_64, Python 3.11+, Git, Bubblewrap with user/PID/mount/network
namespaces, C/C++ compiler, GNU Make, Perl, M4, Bison and Flex. Supply unpacked **private**
toolchain roots with a `bin/` directory. Node must be 22.22.1, its npm 10.9.4, and Go
1.26.0. Wrong pins fail before dependency installation. Native toolchains are recorded by
build output; this implementation does not claim bit-reproducible binaries. macOS and
Windows execution are unsupported by this adapter; the older macOS results remain
historical evidence only.

A fresh checkout needs no original corpus. For example, from the toolkit root:

```sh
uv run python -m benchmarks large list
uv run python -m benchmarks large prepare --output /absolute/new/curator
uv run python -m benchmarks large qualify \
  --prepared /absolute/new/curator --output /absolute/new/qualification \
  --toolchain /absolute/tools/go \
  --toolchain /absolute/tools/node-v22.22.1-linux-x64 \
  --toolchain /absolute/tools/native/usr --seconds 3600
uv run python -m benchmarks large status /absolute/new/qualification
```

`prepare` and `qualify` accept repeated `--case ID`; omission selects all four, serially.
Every output directory must be new. Sources, dependencies and compilation are separate for
every control. A partial failure is retained; a retry uses another directory. `qualify`
returns nonzero if any case is unqualified, still recording subsequent cases. No automatic
retry or selection of the best repetition occurs. The command execution budget is per case and shared
by its controls, with smaller per-command deadlines and two compiler workers. Source
verification/export and canaries have their own bounded commands outside that budget;
`--seconds` is not a whole-case staging-inclusive deadline. Captured
stdout/stderr are bounded by the common runner. A free-space check stops between commands
below 2 GiB; **there is no filesystem quota or aggregate memory limit**, so provision and
monitor a dedicated volume. Allow approximately 15–25 GiB for the set and retained failed
attempts; actual costs are in receipts. Heavy builds run serially.

Dependencies alone use the inherited approved HTTP proxy and CA trust. No other inherited
configuration or credential environment is passed. Dependency manifests/lockfiles come
from the pinned source; npm lifecycle scripts are disabled. Builds and tests run with no
host network, with Go module retrieval and npm online mode disabled. Go's affected module
is `exporter/exporterhelper`; root `go test ./...` is not a substitute. Only selected
toolchain roots and system runtime directories are read-only mounts. Home, temporary files
and caches are private. Keep toolchain roots free of source trees, credentials and compiled
project caches. Do not point `--toolchain` at a broad host directory.

Each command receives a fresh PID/network/mount namespace. The namespace permits its own
loopback servers, but cannot reach host loopback or retrieve public answers. Minimal
synthetic passwd/group/hosts files replace host account configuration. Namespace teardown
kills task-owned descendants, including children that create new sessions. Success and
external timeout cleanup, outside reads/writes, symlink aliases, real external Git objects,
a live host listener, and positive local server access are exercised by
`tests/test_large_project_execution.py`. Missing target files or interpreter startup
failures cannot count as successful denial. No isolation downgrade is available.

This isolates **trusted curator controls**. An actor command API is deliberately absent:
the evaluator, hidden tests and receipts are in the curator control root, which is writable
during its own builds. Never give that root or `LinuxBoundary` directly to a candidate.
The existing native Codex actor/budget pipeline still accepts only the small cases. A future
integration must stage only the exported source and independently seal the evaluator and
its test overlays; it must retain the existing shared descendant-budget and prompt-surface
checks. Current namespace tests do not establish that complete agent/evaluator boundary.

## Grading contracts and current limits

`adapters.py` describes commands and roles; `finalize.py` makes narrowly checked evaluator
transformations **identically on every source control**. Upstream tests are reconstructed
from the digest-verified patch; copied test files retain upstream copyright and license
notices. The source tree retains each upstream license. No production fix is applied to
the parent control. Adapted tests and any changed evaluator harness are separately hashed.

- VS Code: exclude the passing private `_snippet` backfill assertion. The six observable
  failures remain, as do undo, differing resolved lengths and caller edit order. Expected
  selected-suite totals are 79 pass/6 fail/1 pending before and 85 pass/1 pending after;
  these **need Linux requalification**. Mocha JSON records individual outcomes and pending
  checks. This is browser editor coverage, not Electron or extension integration. Optional
  Copilot simulation LFS assets stay pointers; their exclusion still needs validation after
  a successful browser run.
- CPython: run the sibling/nested observable regressions three times and six original
  non-memory controls. The deterministic scheduler retains `_blocking_on` and lock
  `name/owner`: it must observe a second thread actually waiting before releasing the first,
  rather than infer that state from a sleep. This is an explicit limitation to lock
  implementations that retain that existing diagnostic interface, not a public Python
  compatibility requirement. Lock-lifetime assertions and the two new `_resolve_parents`
  monkeypatch tests are not acceptance gates. Five upstream memory-heavy controls are
  separate diagnostics, with skips recorded rather than counted as passes. Builds are
  fresh debug/GIL builds, regenerate frozen importlib, and verify the loaded source path.
  Module availability appears in build receipts. The full seven historical fixed suites,
  other architectures and free-threaded builds are not claimed here.
- Collector: keep deterministic `L`/`Wait`/`Signal` coordination, remove `c.waiting` checks
  and the passing queue-lock-injection test. Six existing memory/persistent queue groups and
  notification accounting are pass-to-pass controls. Signal-progress and cancellation
  regressions run three times each. Private channel shape and buffer sizing are unconstrained.
  Qualification also tries an independent per-waiter-channel implementation (no shared
  channel or counter) and a partial fix that only increases the buffer. The latter must
  still fail the overflowing cancellation test. Each has fresh caches and race detection.
  Mock persistent storage does not establish crash durability.
- PostgreSQL: debug/assert builds, private prefixes, ephemeral local servers, three nearby
  controls and three repetitions of the six-schedule race test. For the race test only,
  the evaluator renderer emits SQLSTATE instead of primary error wording; the five required
  dependency errors must be `2BP01`. All prescribed blocking/completion order remains
  constrained. Nearby controls retain their original renderer and golden files. ICU,
  readline and zlib are disabled. No full regression, TAP, recovery or check-world claim.

A required test that skips, disappears, reports an error, compiles unsuccessfully, exceeds
its deadline or discovers zero tests cannot qualify. A parent requires its specified
failures **and** passing controls; exit 1 alone does not establish regression reproduction.
A reference requires every required gate to pass. Reference-only diagnostics are labeled
separately. No textual patch-similarity or terminology score is used. VS Code's pending
upstream test is explicitly reported and excluded from required gates.

## Evidence and cleanup

Each side retains numbered JSON command receipts with exact argv/cwd, non-secret environment
choices, exits, stdout/stderr, timeouts, elapsed time, discovered outcomes and classifications.
`qualification.json` records tool/source/test/control/runner identities, cold setup and warm
test costs separately, platform and isolation canaries. `evidence-sha256.json` binds the
receipts and summary. These hashes detect accidental changes, not an operator rewriting
both files. Code changes during a qualification invalidate its runner provenance.
Bulky sources, caches, installations and logs stay outside Git. A sanitized committed
summary cannot substitute for the original logs it references.

Export only the untouched broken source for inspection:

```sh
uv run python -m benchmarks large export --case cpython-import-locks \
  --curator /absolute/new/curator/cpython-import-locks --output /absolute/new/source
```

The export comes from the parent's immutable Git tree, excluding Git metadata, added hidden
tests, curator build artifacts and caches. It includes only the symptom-based task, never
this issue, handoff, fix commit or solution links. Unsafe escaping/chained symlinks are
rejected. An export is **not an isolated candidate environment**; do not run an agent in it
without a verified boundary.

To reclaim space after retaining desired evidence:

```sh
uv run python -m benchmarks large clean /absolute/new/qualification/cpython-import-locks
```

Cleanup removes only known bulky source/build/cache/home/tmp children of a single
qualification directory; it retains all JSON command receipts and summaries. Symlink roots
and side directories are refused. Preparation trees are intentionally not removed by this
command; retain or remove their explicitly selected directories yourself.

Completion of #5 still requires successful finalized grading qualification for all four,
VS Code LFS-exclusion validation, fresh independent verification, and an integrated candidate
actor/evaluator boundary with aggregate budget, filesystem quotas/resource bounds and
separately enforced hidden assets. No comparison study or effectiveness claim is authorized
by these curator commands.
