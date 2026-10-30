# Archived Linux curator qualification record — 29 October 2026

This is the historical pre-integration record for commit `4fa5d4e`. Its results and remaining-work
list describe that revision, including the then-unimplemented integrated pipeline and native
preflight failure. They are not current integrated-runner qualification or a report on later
macOS repairs. The original JSON evidence remains unchanged.

This record supports the curator adapters, not completion of issue #5 or a model comparison.
`linux-summary.json` contains sanitized exact commands, environment choices, source/test/runner
hashes, command exits, counts, costs and every retained development-attempt summary. Original
stdout/stderr and receipts remain outside Git; their hashes identify those external records
but cannot independently authenticate this summary. Re-run the documented CLI to reproduce it.

The cloud host is Linux x86_64 with GCC 14.2.0, GNU Make 4.4.1 and Bubblewrap 0.12.0.
[Private toolchain reproduction](../linux-toolchains.md) records verified Go/Node downloads,
Debian package hashes and Bison relocation. No original local corpus, personal skill library,
model credentials or global toolchain replacement was used.

| Case | Linux result | Evidence and coverage |
| --- | --- | --- |
| VS Code | **Blocked** | Node/npm pins and lockfile installs pass on both sources. Chromium download is denied with HTTP 403 by the approved proxy. Browser regressions, pending-test behavior and LFS-exclusion applicability remain unverified. The expected 86-title evaluator inventory was independently checked statically. |
| CPython | **Qualified with scheduler constraint** | Both observable regressions fail on the parent and pass on the fix in 3/3 repetitions; six controls pass both. Five memory-heavy diagnostics skip both. Fresh debug/GIL builds regenerate frozen importlib and verify its loaded source. |
| Collector | **Qualified** | Both regressions fail before and pass after in 3/3 repetitions, with seven passing control groups. The independent per-waiter-channel implementation also passes; enlarging only the buffer still fails cancellation. Fixed and alternative full queue packages pass with race detection: 51 top-level tests each, including descendant checks. |
| PostgreSQL | **Qualified** | Fresh debug/assert builds: all six schedules differ on the parent and match on the reference in 3/3 repetitions. Three nearby controls pass both. SQLSTATE comparison preserves dependency-error semantics while retaining prescribed blocking and completion order. |

CPython's actual Linux build reports `_sqlite3` disabled and 12 optional modules missing:
`_bz2`, `_ctypes`, `_ctypes_test`, `_curses`, `_curses_panel`, `_dbm`, `_decimal`, `_gdbm`,
`_lzma`, `_tkinter`, `_uuid`, `readline`. No failed-on-import module is reported. This is not
the historical macOS optional-module set. Seven full historical suites, free-threaded builds
and other platforms were not revalidated. The deterministic scheduler still reads the
documented existing private lock observation interface; arbitrary lock representations
are not claimed to be accepted.

Source exports for all four cases were checked against untouched parent Git blobs. They
contain no `.git`, added hidden tests, curator caches or reference fix metadata. Actual
namespace tests verify outside-file/symlink/Git-object denial, a live host-loopback denial,
positive local server use and descendant termination on success, nonzero exit, timeout and
controller SIGINT. Chained export symlinks and read-only Go-cache cleanup have regression
controls. These tests establish the curator command boundary, not an integrated agent runner.

## Independent review and verification

A separate generic read-only reviewer found five substantive grading/provenance issues in
the first diff: aggregate-only browser scoring, skipped Go descendants, internal-timeout and
SQL-harness false negatives, missing preparation-timeout receipts and incomplete provenance/
budget scope. They were corrected and re-reviewed. Actual PostgreSQL TAP parsing and
read-only Go-cache cleanup were subsequently corrected. Long Unix socket paths were
fixed by using the namespace-private `/tmp`; their setup failures were retained. Final review reports no actionable
findings in the reviewed code delta.

A separate generic verifier used a fresh source copy without `.git` or `.venv`, rather than
relying on writer assertions. It independently prepared/exported the pinned Collector source,
checked the evaluator/source hashes, and replayed actual CPython and all four Collector
controls in fresh namespaces. It also regraded the retained CPython/Collector receipts with
the final scorer; every verdict was unchanged. The verifier also checked all 112 sanitized command rows against raw receipts, independently
replayed PostgreSQL on both revisions and verified server cleanup. No named custom-role
loading is claimed. `independent-checks.json` records the separate verifier artifact hashes.

Repository checks at the archived revision:

- `uv sync --group dev --frozen` — passed.
- `uv run python -m unittest discover -s tests -p 'test_large_project*.py' -v` — 33 passed.
- Full suite with a same-filesystem `TMPDIR` — 179 tests, two errors. Both native
  `NativeExecutor.preflight` hardlink-canary errors reproduce on pristine starting commit
  `71bda87809ed31250aba91a6e7f4f4362aea845a`, with Codex CLI 0.163.0 on this host. The canary
  raises `FileNotFoundError` for the forbidden hardlink target. Isolation was not weakened
  to bypass these failures. Full-suite success and native candidate readiness are not claimed.
- Ruff check/format, mypy (22 files), `python3 install.py check` — passed.
- `uv run python -m benchmarks validate` — all 13 existing control phases passed.
- `git diff --check` — passed.

The first default `/tmp` full-suite attempt also encountered installer hardlink `EXDEV`
errors; selecting a temporary directory on the workspace filesystem resolved those. Failed
preparations, parser versions, a task-owned interrupted correction build and cleanup failures
are retained and summarized instead of being replaced by successful later attempts.

## Remaining work

Issue #5 stays open. Chromium's `cdn.playwright.dev` and
`playwright.download.prss.microsoft.com` downloads need permitted access before VS Code can
be qualified. Large-project cases are deliberately unavailable to model planning/grading:
the separate candidate/evaluator integration, hidden-asset enforcement, inherited-guidance/
source-arm staging and aggregate descendant-budget verification are not implemented here.
There is no filesystem quota, aggregate memory bound or staging-inclusive wall deadline.
The existing native actor preflight also fails on this host as reported above.

No comparison study, paid infrastructure, upstream contact, merge or effectiveness claim
was performed.
