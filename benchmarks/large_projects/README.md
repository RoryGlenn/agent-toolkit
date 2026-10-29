# Large-project benchmark cases

The four public historical regressions for [issue #5](https://github.com/RoryGlenn/agent-toolkit/issues/5)
extend the existing benchmark CLI, arm staging, native budgets, frozen artifacts and reports.
This directory is **curator material containing answers**. It must never be mounted in an
actor cell. No comparison study has been run. The current [verification record](verification/README.md)
states which qualification gates have actually executed; unavailable gates do not establish readiness.

`catalog.json` pins the untouched parent, reference revision, digest of the upstream test-only
patch, symptom task and known limitations. `prepare.py` reconstructs the curator worktrees
and verifies the direct parent and patch identity. `adapters.py` defines the executable
commands; `finalize.py` applies the same audited grading adaptations to every submission.
Older macOS results in `prior-qualification.json` and `command-recipes.json` are historical,
not Linux proof. Upstream licenses remain in every source export and copied test file.

## Supported environment and preparation

The integrated runner requires Linux x86_64, Python 3.11+, a local Docker daemon with cgroup v2,
user/mount/PID/network namespaces, Bubblewrap, and the **full matching Codex CLI 0.165.0
package** including `codex-code-mode-host` and `codex-resources/bwrap`. A standalone CLI
binary is insufficient. System C/C++ tools, Make and Perl must be installed. Supply private
Go 1.26.0, Node 22.22.1/npm 10.9.4, and Bison/Flex/M4 roots as needed; see
[toolchain reproduction](linux-toolchains.md). Do not select a broad host home, curator
source or compiled project cache as a toolchain. macOS/Windows large-project execution is
unsupported. Small RecordBatch cases retain their existing interfaces.

The local resource image is pinned by digest in `resources.py`. Pull that exact image using
the environment's approved Docker configuration before qualification. The runner never
changes Docker endpoints, uses host networking, mounts its socket into cells, disables TLS,
or bypasses the environment's network policy. Docker's configured proxy and CA trust must
be available for dependency prefetch and the separate model-client transport.

```sh
uv sync --group dev
uv run python -m benchmarks large prepare --output /absolute/new/curator
uv run python -m benchmarks large runtime-check \
  --codex /absolute/codex-package/bin/codex --output /absolute/new/runtime-proof
uv run python -m benchmarks large prefetch --case otel-queue-cancellation \
  --curator /absolute/new/curator/otel-queue-cancellation \
  --toolchain /absolute/tools/go \
  --output /absolute/new/dependencies/otel-queue-cancellation
uv run python -m benchmarks large prefetch --case vscode-snippet-selections \
  --curator /absolute/new/curator/vscode-snippet-selections \
  --toolchain /absolute/tools/node-v22.22.1-linux-x64 \
  --chromium /usr/lib/chromium/chromium \
  --output /absolute/new/dependencies/vscode-snippet-selections
uv run python -m benchmarks large qualify \
  --prepared /absolute/new/curator --output /absolute/new/qualification \
  --dependencies /absolute/new/dependencies \
  --toolchain /absolute/tools/go \
  --toolchain /absolute/tools/node-v22.22.1-linux-x64 \
  --toolchain /absolute/tools/native/usr --seconds 3600
uv run python -m benchmarks large status /absolute/new/qualification
```

`prepare` and `qualify` accept repeated `--case`; omission selects all four serially. Every
output directory must be new. Failed attempts, command receipts and explanations remain
available. There are no automatic retries or best-of-many selection. Heavy builds are
serialized with two compiler workers and two CPU equivalents per cell. Allow roughly
15–25 GiB of controller disk for source/dependency bundles and retained evidence. Cleanup
is explicit; the runner never deletes unrelated work to make space.

Prefetch runs only from the verified untouched parent with npm lifecycle scripts disabled.
It exports only Go module source, root/build npm dependencies and the Playwright browser
installation, as applicable. Complete inventories and receipts bind these inputs to their
parent. Every actor/evaluator starts with an empty project compilation cache. Verified
source/dependency bundles may be reused; compiled reference output is never an actor input.
For VS Code, the optional explicit `--chromium` mode uses the already installed Linux
Chromium **154.0.8037.57** at `/usr/lib/chromium/chromium`. It binds the executable version
and complete runtime-directory fingerprint, executes a real DOM smoke, and passes the
explicit executable path to the browser harness identically on parent/reference/candidates.
It neither downloads a replacement nor poses as Playwright's default cached browser. The
selector and runtime identity are included in dependency/qualification/plan provenance.
Omitting it retains the locked Playwright download mode, which needs the environment
allowlist for `cdn.playwright.dev` and `playwright.download.prss.microsoft.com`. A policy
denial is a setup failure; no alternate download route is supplied. The selected VS suites
must qualify on the actual chosen browser before planning.

CPython and PostgreSQL require no separate dependency bundle. A missing browser download or
native library is a setup failure, never a negative regression control.

## Kernel limits and cleanup

Every attempt has one external monotonic wall deadline covering source verification,
staging, native preflight, execution, freezing and grading. Dependency prefetch is a separate
unscored operation with its own deadline. Qualification shares its deadline across all
controls. A watchdog process kills a blocked staging worker and removes only containers and
volumes bearing that attempt's unpredictable ownership label. Cleanup has a separately
bounded grace period and remains recorded on timeout, cancellation, success and failure.

Cells use a readonly image and readonly system/toolchain mounts, no capabilities, a private
PID/cgroup namespace, no-new-privileges, a process ceiling, `memory.max`, zero swap and a CPU
quota. Workspace, temporary files and shared memory use size-limited tmpfs. All descendants
share the same limits. Staged writable pages are copied again **inside the cell cgroup** so
Docker's upload cannot leave mutable input pages charged to its daemon.

The native sandbox needs eight namespace/mount syscalls added to the vendored, attributed
Docker default seccomp profile. It retains all other default restrictions; no privileged or
unconfined seccomp mode is used. Because a nested user namespace can mount another tmpfs,
the supported native profile requires **equal memory and filesystem ceilings** (default
8 GiB each). The global memory cgroup bounds every allocated writable tmpfs page, including
extra mounts; anonymous memory and filesystem pages share that ceiling. The filesystem
contract covers allocated data, not sparse logical lengths. Readonly input/system mounts
are excluded. This is a stricter combined allowance, not an independent 8 GiB RAM plus
8 GiB disk allowance. Kernel ENOSPC, forked OOM, pid exhaustion and extra nested tmpfs
controls execute in `runtime-check`. A pinned Docker seccomp profile and mount layout are
part of harness provenance.

Model-client transport is separate from command networking. Actual native tools use the
managed proxy with only `localhost` and `127.0.0.1` allowed, plus a private raw network
namespace. Local HTTP/TCP harnesses work; host listeners and nonlocal retrieval are denied.
Connectors, web, plugins, browser tools, memory, hooks and escalation remain disabled.
`runtime-check` drives real Code Mode tools using a scripted local Responses server with no
model, auth or paid call. It proves positive workspace/readonly/local-network access and
denial of protected config, aliases, `/proc` escapes, Git objects and a live host listener.
A real parent/child session tree exhausts a 50-unit native budget at 70 observed units,
recording its 20-unit completion-boundary overshoot. Configuration parsing alone is no gate.

## Candidate and evaluator pipeline

The common `plan`, `prepare`, `run`, `grade` and `report` operations handle large cases.
Planning requires `--large-context CONTEXT.json`, an explicit large case and descendant
budget. Context selects prepared sources, completed current qualification, runtime proof,
toolchains, verified dependency bundles and optional resource limits:

```json
{
  "prepared": "/absolute/new/curator",
  "qualification": "/absolute/new/qualification",
  "runtime_qualification": "/absolute/new/runtime-proof/runtime-qualification.json",
  "toolchains": ["/absolute/tools/go", "/absolute/tools/node-v22.22.1-linux-x64", "/absolute/tools/native/usr"],
  "dependencies": {
    "otel-queue-cancellation": "/absolute/new/dependencies/otel-queue-cancellation",
    "vscode-snippet-selections": "/absolute/new/dependencies/vscode-snippet-selections"
  }
}
```

Every selected case must have complete, checksum-verified qualification matching the current
harness. Missing, skipped or unexecuted gates block planning. Runtime and source identities
are rechecked during the attempt. These commands are infrastructure; a model comparison
requires separate authorization and is not part of issue #5 qualification.

The existing three arm layouts are reused. Original parent project guidance is retained
equally across arms; books and toolkit entry points follow the existing source profiles.
Only the parent export, selected arm resources and verified dependency inputs enter the
actor. It receives no Git history, added hidden tests, curator fixture, reference answer,
result receipt or compiled reference cache. Auth is explicitly selected by the operator,
provisioned after model-free native preflight into the protected client home, and removed
when the invocation ends. Prompt/tool discovery is inspected before a model call.

After execution the controller pauses **every** actor descendant. A named tmpfs volume
provides a stable nonempty archive while paused. Candidate tar entries are read as data;
they are never extracted on the host. Traversal, duplicate entries, hardlinks, changed source
symlinks and special files fail closed. The frozen artifact records changed ordinary
production files, deletions, parent fingerprint and excluded test/build changes. Per-file,
delta, archive and output bounds apply. The actor and its detached children are destroyed
before any hidden assets are staged.

Grading exports a new parent, verifies/applies the frozen production delta, then restores
the pinned authoritative tests and audited adaptations. It rebuilds in a separate cell with
readonly source, hidden checks, build scripts and dependency inputs. VS Code's trusted
transpiler may replace `out/`; the generated output is readonly during testing. Candidate
tests and build scripts cannot replace authoritative checks. No candidate Python is imported
into the controller. The Bubblewrap launcher keeps a trusted parent alive through `docker
exec`, retaining parent-death protection and namespace teardown.

The declared production scope is the affected component: VS Code snippet browser sources;
CPython importlib and import C/internal headers; Collector queue Go sources excluding test
files; PostgreSQL command/catalog/locking C and include headers. These scopes are explicit
in `artifacts.py`. The exact non-solution scope and ignored-file contract are included in every candidate
TASK.md. Tests and build/configuration changes are retained for review and excluded from
authoritative grading. Production-source edits outside the component fail the scope gate. This is a
component repair benchmark, not an unrestricted whole-repository patch acceptance service.
The evaluator measures behavior, not patch similarity. Maintainability remains a separate
independent review dimension.

A frozen delta can be graded without a model:

```sh
uv run python -m benchmarks grade /absolute/frozen/artifact \
  --case otel-queue-cancellation --curator /absolute/new/curator/otel-queue-cancellation \
  --dependencies /absolute/new/dependencies/otel-queue-cancellation \
  --toolchain /absolute/tools/go --seconds 1800 --output /absolute/new/grading
```

Model-free `large qualify` runs parent/reference production outputs through this same
freeze/transfer/rebuild/grading path. Its trusted control writer alone receives reference
production bytes; no agent is launched. Added tests and answer-bearing curator state never
enter that source-output cell. Qualification also evaluates Collector alternative and partial
fix controls. Failures, timeouts, setup errors, missing tests and known pending checks remain
distinct in receipts and the existing reports.

## Grading contracts and limits

- VS Code excludes the passing private `_snippet` backfill assertion. Six observable
  regressions retain undo, differing resolved lengths and caller edit order. Expected
  selected-suite totals are 79 pass/6 fail/1 pending before and 85 pass/1 pending after.
  Mocha JSON binds every test identity; the sole unchanged upstream pending check is reported
  and excluded from required gates. This covers the browser editor, not Electron/extensions.
  The optional unrelated Copilot simulation LFS assets remain pointers; successful Linux
  qualification must demonstrate that this exclusion does not prevent the selected suites.
- CPython runs two sibling/nested observable regressions three times plus six non-memory
  controls. Its deterministic scheduler retains `_blocking_on` and lock `name/owner` to
  prove a thread is waiting; no flaky sleep substitutes for coordination. This remains an
  explicit diagnostic-interface constraint. Lock-lifetime and new `_resolve_parents`
  monkeypatch tests are excluded from acceptance. Five memory-heavy tests are separate
  diagnostics with skips reported. A fresh debug/GIL interpreter regenerates frozen importlib
  in its build directory and verifies its loaded source path. The test cleanup helper checks
  whether a pyc exists before unlinking it: Linux returns EROFS for absent files on readonly
  mounts. Existing-file cleanup failures remain errors. Full suites, free-threaded
  builds and other architectures are not claimed.
- Collector keeps deterministic `L`/`Wait`/`Signal` coordination and removes counter checks
  and queue-lock injection. Six memory/persistent groups and notification accounting are
  pass-to-pass controls. Both regressions run three times each with race detection. An
  independent per-waiter-channel implementation must pass; a larger-buffer partial fix must
  still fail cancellation. Full correct queue packages run as diagnostics. Mock persistent
  storage does not establish crash durability.
- PostgreSQL uses debug/assert builds, private prefixes, ephemeral servers, three nearby
  controls and three repetitions of all six race schedules. Race errors compare SQLSTATE
  `2BP01`; required waiting/completion order remains constrained. Nearby controls retain
  their original renderer. ICU/readline/zlib are disabled. No full regression, TAP, recovery
  or check-world coverage is claimed.

For scored submissions, ordinary compiler diagnostics become candidate build failures.
Signals, resource/runtime faults and incomplete output remain distinct environment failures;
a failed trusted-control build cannot establish regression reproduction.

Required tests cannot skip, disappear, report errors, time out, compile unsuccessfully or
execute zero tests and still qualify. Parent exit 1 alone is insufficient: the expected
behavioral failures and all passing controls must be observed. Reference-only diagnostics
are separately labeled. Every attempt records commands, tool versions, non-secret environment
choices, source/test/harness identities, executed outcomes, exits, resource events and costs.
Unknown aggregate real-model usage, overshoot or cost remains null; null never means zero.
A common cap is not a claim of equal exact tokens, compute or dollars.

## Evidence and cleanup

`qualification.json` and numbered receipts retain each side's outcomes, cold setup and warm
test costs. `evidence-sha256.json` binds the retained summaries and command receipts. These
checksums detect changes, not a malicious operator rewriting both evidence and checksums.
Bulky sources/caches/builds and private traces stay outside Git. Sanitized committed summaries
identify their original records and do not replace them. Source changes during qualification
invalidate readiness; a new output directory is required for the next attempt.

`large export --case ID --curator DIR --output NEW` still exports only the pinned untouched
parent for inspection, without Git history or added hidden tests. An export by itself is
not an isolated execution environment.

`large clean /absolute/qualification/CASE` removes only known runner-owned bulky trees and
retains receipts. Symlink roots/ancestors are refused. Preparation and dependency bundles
remain operator-owned. Never delete failed evidence, unrelated work, or a source clone to
hide a qualification problem. Issue #5 stays open while any required case gate is unverified.
