# Final independent review: personal status and shared CLI integration

Reviewed the final uncommitted product diff in `work/agent-toolkit` against `0b36e7d4e95300b16a713edf831c8613dba46b69`, after the integration writer stopped. The review focused on personal status, its path-loop correction, and shared parser/dispatch interactions with `list --json` and `bootstrap --check`. No product source was edited and no work was delegated. Earlier frozen-candidate findings remain unchanged in their original report.

## Findings

**No remaining actionable findings or blockers in the reviewed scope.**

The previous path-loop failure is corrected at `install.py:830`: `RuntimeError` is converted to `InstallError` only while resolving personal-status paths. The outer handler then emits the existing JSON failure response and stderr diagnostic. The change does not broadly catch unrelated runtime errors or alter installation's handling of them.

The status implementation retains canonical absolute skill-link checks, regular-file/current-source-inode role checks, dependency closure and deduplication, explicit-home semantics, Copilot skill-only results, sorted entries, and appropriate exit codes. The installed-state, missing/foreign-entry, stale-hardlink, and read-only tests remain effective after integration.

The shared parser guards status-specific JSON error handling with the command name. `bootstrap --check` validates incompatible flags before dispatch and runs before package inventory, while `list --json` and ordinary list/install/bootstrap paths retain their own dispatch. Inspection found no attribute-access or exception-routing regression between these commands.

## Verification performed

From `work/agent-toolkit`, with the supplied Python environment and temporary directory:

```text
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python -m unittest discover -s tests -p test_install.py
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python -m unittest discover -s tests -p test_project_bootstrap.py
git diff --check 0b36e7d4e95300b16a713edf831c8613dba46b69
```

- Installer suite: **60 tests passed**, 3.945 seconds.
- Project bootstrap suite: **29 tests passed**, 6.624 seconds.
- Diff whitespace check: **passed**.
- Independently recreated a self-referential symlink in a disposable directory and launched the real CLI twice, once with `--home` pointing to it and once with `--codex-home` pointing to it. Both returned `1`, emitted exactly one parseable JSON object with `schema_version: 1`, empty `entries`, and a loop diagnostic in `error`, and printed a concise stderr diagnostic without a traceback. No inspection home was created.
- Independently bootstrapped a disposable project, removed the disposable toolkit's current `skills` and `agents` trees, and ran `bootstrap --check`. It returned `0` and verified the recorded 32 managed files plus routing block, confirming dispatch bypasses current source inventory.
- Independently exercised `list --json`, missing Copilot `status --all --json`, `bootstrap --check`, and `list --json` sequentially through one loaded CLI module. Results and JSON remained correct with both initial values of `sys.dont_write_bytecode`, and each call restored that global state. The missing inspection home remained absent.
- Reviewed the complete `install.py` diff, affected test changes, the integrity-check dispatch and implementation changes in `project_bootstrap.py`, and the new bootstrap tests.

The newly added subprocess test `test_status_json_symlink_loop_homes_fail_without_writes` covers both path options, a single JSON result, exit status, absence of traceback, and a complete before/after filesystem snapshot.

Reviewed source bindings:

| File | SHA-256 |
| --- | --- |
| `install.py` | `8939b775f65abee7896916e6d420e5c25105d51b1e2592a0f556d218fe0682ac` |
| `project_bootstrap.py` | `06af22a0081f8ecf15244044d3c9bd46d4bf4d440d782f8971948d513bf82598` |
| `tests/test_install.py` | `b5bd5172a0506b89e26fb9b2e44936992a13ea91d0da644ae0b61c2e1c3cb55f` |
| `tests/test_project_bootstrap.py` | `f70f294294d00516d4579ee222064f4f948b89094c91156606298b05f6c324a2` |

## Unverified risks

This review did not run the full repository check suite, an alternate Python/platform matrix, or concurrent-filesystem stress tests. Status remains a documented point-in-time observation rather than an atomic filesystem snapshot. Broader integrity-check semantics and catalog schema are outside this specialist review except where their integration affects status and shared CLI behavior.

## Verdict

**ready** for the reviewed personal-status and shared CLI integration scope.
