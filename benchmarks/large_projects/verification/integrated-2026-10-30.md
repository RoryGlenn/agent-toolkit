# Integrated verification record — 30 October 2026

**Status: unqualified.** The macOS scratch-boundary repair is verified, but the integrated
Linux runtime and four large-project case gates remain unverified. Issue #5 remains open.
This record distinguishes source preparation, local tests and actual Linux qualification.
The [archived curator results](README.md) at `4fa5d4e` do not qualify the integrated runner.

## Local repair and repository checks

An independent verifier used macOS arm64 with the actual Codex CLI 0.166.0. On baseline
`5a0017411a2df43f0965467e57cce47d4e4a126f`, the public preflight succeeded but subsequent
execution could read/write unrelated global temporary canaries and create sibling files.
The same differential check passed after the six-file repair later committed as
`91b35c25b90c9e24f6fff39093c7e8ad240a9407`. It preserved narrow workspace/private-temporary
writes and readonly reads while denying access through canonical and lexical aliases of
both `/tmp` and `/var/tmp`. Both network-profile configurations were checked.

After integration with main `0b36e7d4e95300b16a713edf831c8613dba46b69`, an independent clean
source copy at `7220856bd7d4620905151d8f92b5333a6fb8ea8c` ran the complete unit suite using
the default macOS temporary directory: **259 run, 252 passed, seven Linux-only skips, zero
failures or errors**. Sync, Ruff lint/format, mypy, strict driver mypy, authoring checks,
upstream verification, package validation, the 13 existing benchmark control phases and
diff checks passed. These local checks do not establish Linux kernel enforcement.

Revision `eb7cbce688877841942b44335e2cc0f2b4824708` added failure diagnostics and receipt
collection. Its focused large-project suite ran 54 tests with seven Linux-only skips and
no failures or errors; lint/type checks passed. The complete 259-test independent result
above belongs to `7220856`, not this later revision.

## Actual Linux attempts

Both model-free attempts used the existing GitHub Actions Ubuntu 24.04 runner. The latest
attempt reported Ubuntu 24.04.5 LTS, Linux 7.0.0 (Azure), x86_64, and the full pinned Codex
CLI 0.165.0 package. Private Go/Node and system build/browser prerequisites were provisioned;
all four pinned curator source preparations completed. The configured resource profile and
required pass conditions were retained.

| Attempt | Exact source head | Observed result |
| --- | --- | --- |
| [41106899263](https://github.com/RoryGlenn/agent-toolkit/actions/runs/41106899263) | `7220856bd7d4620905151d8f92b5333a6fb8ea8c` | Runtime `setup_error`: nested allocated-storage control did not hit its memory cgroup. Cleanup complete. The initial record lacked the nested command diagnostics. |
| [41107537425](https://github.com/RoryGlenn/agent-toolkit/actions/runs/41107537425) | `eb7cbce688877841942b44335e2cc0f2b4824708` | Runtime `setup_error`: nested tmpfs `libc.mount` failed with `EACCES` (errno 13); process exit 1, all recorded memory events zero. Cleanup complete. |

The second run's `receipts/runtime/resources/nested-tmpfs.json` artifact preserves the actual
command, stdout/stderr and memory events. Its line-8 mount failed before allocating the
nested filesystem. The responsible security enforcer is unknown. This is a host prerequisite
failure, not an observed storage-limit
bypass. The required exit 137 plus at least one `oom_kill` event was not relaxed.

Dependency prefetch, actual native-tool/descendant-budget controls and all four integrated
case-grading qualifications were **not reached**. No model calls, comparison study or
benchmark-effectiveness result was produced. Logs, partial receipts and cleanup outcomes
remain in the linked runs' qualification artifacts; they are not replaced by this summary.
The failed-attempt execution evidence remains retained; serialized exports do not recreate
original controller byte formatting.

Artifact indices from these two runs use `sha256`/`bytes` for original receipt bytes before
serialization/redaction. The accompanying collector correction names both identities:
`source_sha256`/`source_bytes` and `exported_sha256`/`exported_bytes`. Exported identity fields
verify the actual uploaded bytes. This metadata correction is not another Linux execution.

## Remaining qualification

Further qualification requires an existing Linux host that permits the required nested
user/mount-namespace and tmpfs operations under the [documented profile](../README.md#supported-environment-and-preparation).
Use the existing serial CLI and fresh output directories on that host. Host security policy,
container restrictions and kernel pass conditions must remain intact. Native runtime/budget
proof and all four complete case gates are required before the integrated runner qualifies.
