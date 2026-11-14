# Independent review: personal installation status

Reviewed frozen candidates `a` and `b` against baseline `0b36e7d4e95300b16a713edf831c8613dba46b69`, using the independent-diff-review skill and the supplied requirements. No writer summary, condition mapping, or planning artifact was inspected. No implementation was edited and no review work was delegated, as instructed.

The clarified contract permits an additional JSON `error` field on failures and does not require argparse syntax failures to emit JSON. Neither difference is treated as a finding.

## Findings

### Low — Both candidates omit JSON when a supplied home contains a symlink loop

- **Locations:** `a/install.py:751` and `a/install.py:777`; `b/install.py:767` and `b/install.py:799`, in `main`.
- **Broken invariant:** A syntactically valid `status ... --json` invocation with an invalid filesystem layout should produce one JSON result and a nonzero exit. `Path.resolve()` raises `RuntimeError` on a symlink loop in the supported Python runtime. Both exception handlers omit that exception, so these requests instead produce an uncaught traceback and empty stdout. A caller cannot parse the promised status response.
- **Reproduction:** Create a symlink `loop` whose target is itself, then run `python install.py status --target codex --skill documentation-skill --home /absolute/path/to/loop --json`. Against both frozen candidates the observed return code was `1`, stdout was `''`, and stderr ended with `RuntimeError: Symlink loop from '.../loop'`. A looping explicit `--codex-home` reaches the same resolution path.
- **Smallest safe correction:** Convert the path-resolution `RuntimeError` to `InstallError`, or include it in the CLI's existing status error handling, so the JSON failure response is emitted. Add a CLI regression covering a looping supplied home and Codex directory, asserting exactly one JSON object, nonzero exit, a stderr diagnostic, and no filesystem changes.
- **Current tests:** Neither candidate tests a loop during resolution of the supplied home or Codex home. The existing invalid-parent tests use a resolvable destination-parent symlink, which reaches `check_parents` and cannot detect this failure.

No other actionable correctness, compatibility, linkage, selection, or read-only defect was found in the reviewed sources.

## Verification performed

Commands used the supplied virtual environment and temporary directory:

```text
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/pilot-tmp /home/ubuntu/Documents/Codex/2026-10-31/new-chat-4/work/dev-venv/bin/python -m unittest discover -s tests -p test_install.py
```

- Candidate `a`, run from its frozen root: **54 tests passed**, 2.376 seconds.
- Candidate `b`, run from its frozen root: **54 tests passed**, 2.910 seconds.
- A separate subprocess probe created only a temporary self-referential home symlink and ran the exact valid status arguments described above for each candidate. Both reproduced the finding.
- Inspected the CLI dispatch, existing installation selector path, canonical alias/dependency closure, inventory validation, destination ancestor checks, exact skill link comparison, role regular-file/inode checks, sorted/deduplicated output, exit behavior, Copilot skill-only mapping, and the new tests and documentation.
- Reviewed the current-source hardlink cases, including copied/equal-byte roles, role symlinks, stale hardlinks after atomic replacement, and foreign links. Both implementations enforce the required distinctions and avoid treating linkage as overwrite permission.

Source bindings:

| Artifact | SHA-256 |
| --- | --- |
| `personal-status-a.patch` | `90820a8c1590956b5525bc1ec041d48812c7a96d25b8051c381b28c3999dd973` |
| `personal-status-b.patch` | `a0ffa152bf8c12f21666cacc7cf61e7b40c5bf2359452840438c88957963723f` |
| `a/install.py` | `c00c55d27289848fcc222fcc9a2ea7d1db9f265dab9719473ede95677b549068` |
| `a/tests/test_install.py` | `0744e0860f215b6d96b0a6fd81f8981f0fde7a94051e75e8c78d69b30d0345bb` |
| `b/install.py` | `ca78ba9efd7d240cd59b305c76122db31dba4fa58c820117ff4f26470e236689` |
| `b/tests/test_install.py` | `35e4df027792da812292d6855690e3b3f793cdc9fb4555157001eaac85c31028` |

## Code quality comparison

Both changes are compact and reuse the existing selector and path machinery without adding dependencies or persistent state. Candidate `a` reuses the established `linked_to` predicate after checking destination type, and centralizes bytecode suppression in the shared selector helper. Candidate `b` spells out the status-specific link checks and limits bytecode suppression to inspection. Both are understandable and preserve existing installation behavior in the exercised suite.

Candidate `b` checks full filesystem snapshots across more individual status scenarios and adds machine-readable argparse-error tests. Candidate `a`'s fresh-process snapshot test checks both absent and installed destinations, including existing receipts. These are complementary test strengths; neither covers the shared path-resolution failure above. The review found no substantial implementation-quality separation beyond these small structural and coverage differences.

## Unverified risks

No full repository check suite, alternate Python/platform matrix, or concurrent-mutation stress test was run. Both implementations document status as a point-in-time observation; the reviewed code cannot make the filesystem snapshot atomic. The review and subprocess verification were performed by this independent reviewer, without a second delegated verifier because delegation was explicitly prohibited for this assignment.

## Verdict

`a`: **ready_with_corrections**.

`b`: **ready_with_corrections**.

The required correction is the shared low-severity JSON error-handling gap above.
