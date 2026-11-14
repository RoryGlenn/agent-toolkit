# Final independent review: integrated catalog and project integrity features

## Findings

No remaining actionable findings in the reviewed catalog/project features or their shared CLI integration.

The integrated implementation preserves the accepted catalog JSON contract and unchanged default catalog output. Project integrity checking validates recorded provenance, rejects the five prohibited flag combinations, reads recorded content independently of live source packages, and uses the existing safe file and managed-block helpers. The previously reported malformed-provenance false success in frozen project-check/b is absent: the integrated project_bootstrap.py is byte-identical to reviewed project-check/a.

## Reviewed state and scope

Baseline: `0b36e7d4e95300b16a713edf831c8613dba46b69`.

Reviewed the integrated uncommitted product changes in `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/agent-toolkit`, including shared parsing and dispatch in install.py, catalog JSON generation, manifest validation, integrity checking, and their relevant tests. Inspected the status integration sufficiently to assess parser/dispatch compatibility with list, package check, bootstrap, install, and restore. No implementation edits or further delegation occurred. The original frozen review is unchanged. Generated .agents/openspec content and condition mapping were not inspected.

Exact reviewed file SHA-256 values, confirmed unchanged after verification:

| File | SHA-256 |
| --- | --- |
| install.py | `8939b775f65abee7896916e6d420e5c25105d51b1e2592a0f556d218fe0682ac` |
| project_bootstrap.py | `06af22a0081f8ecf15244044d3c9bd46d4bf4d440d782f8971948d513bf82598` |
| tests/test_install.py | `b5bd5172a0506b89e26fb9b2e44936992a13ea91d0da644ae0b61c2e1c3cb55f` |
| tests/test_project_bootstrap.py | `f70f294294d00516d4579ee222064f4f948b89094c91156606298b05f6c324a2` |

## Verification performed

From the integrated repository, using `/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python -B` and `TMPDIR=/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp`:

| Command after Python | Result |
| --- | --- |
| `-m unittest discover -s tests -p test_install.py` | 60 tests passed |
| `-m unittest discover -s tests -p test_project_bootstrap.py` | 29 tests passed |

Additional narrow Python probes used the integrated module and disposable fixture directories:

- Loaded install.py directly from the baseline Git object with its ROOT set to the same unchanged package assets, and compared default list stdout with the integrated CLI: byte-for-byte identical, exit 0, empty stderr.
- Parsed integrated list --json and checked exactly the top-level and per-entry key sets, schema version 1, name ordering, sorted direct SKILL_DEPENDENCIES, and the supported host set. The integrated installer tests separately cover runtime role names, role ordering, live metadata, dependency failure, escaped descriptions, and read-only output.
- In one Python process, invoked status --json, list --json, bootstrap --check, list, and package check in sequence against an isolated source and project. All expected exit codes and outputs held. Source/project/home snapshots including mode, inode, mtime, link target, and bytes were unchanged; sys.dont_write_bytecode was restored after every call.
- Repeated the three prior malformed-provenance cases: missing source, source as a string, and invalid commit/dirty/hash field types. Each now exits 1, emits no stdout, and reports invalid source provenance, without changing the target.
- Exercised --check with each of --update, --dry-run, --all, --skill, and --target. All five exit 2 with the incompatible-flags diagnostic and no target changes.
- Removed the disposable source's skills and agents directories. bootstrap --check still succeeded from the installed record. list --json and status --json both correctly rejected the invalid live package, showing no cross-command caching bypass. Inspection calls left the remaining source and target entries unchanged.

These probes supplemented, rather than replaced, the existing/new test coverage for changed/missing owned content, managed routing block corruption, malformed/unsafe manifest paths, symlink refusal, unbootstrapped targets, and nested vendored-source cache behavior.

## Unverified risks

This review ran the two relevant integrated suites, not every repository development check. Concurrent filesystem substitution, Windows behavior, and permission-denied reads under a non-root account were not executed. The manifest remains an unsigned integrity record, so coordinated edits to recorded hashes and managed content are outside its stated guarantee.

## Verdict

`ready` for the reviewed integrated catalog/project features and shared CLI compatibility.
