"""Explicit Linux curator commands; historical recipe strings are never executed."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Command:
    """A build or test command and its authoritative discovery contract."""

    name: str
    argv: list[str]
    cwd: Path
    phase: str = "setup"
    timeout: int = 1800
    parser: str = "exit"
    expected: dict[str, str] = field(default_factory=dict)


PYTHON_RUNNER = """import json, sys, unittest
names = sys.argv[1:]
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
r = unittest.TextTestRunner(verbosity=2).run(suite)
states = {n: "pass" for n in names}
for group, state in ((r.failures,"fail"),(r.errors,"error"),(r.skipped,"skip")):
 for test, _ in group:
  for name in names:
   if test.id() == name or test.id().startswith(name+" "): states[name] = state
if r.testsRun != len(names): states = {}
print("TOOLKIT_TESTS="+json.dumps(states))
sys.exit(not r.wasSuccessful())
"""

CP_PREFIX = "test.test_importlib.test_threaded_import.ThreadedImportTests."
CP_REGRESSIONS = [
    "test_concurrent_first_imports_of_sibling_packages",
    "test_concurrent_first_imports_of_nested_packages",
]
CP_CONTROLS = [
    "test_import_hangers",
    "test_circular_imports",
    "test_side_effect_import",
    "test_import_failure_race_condition",
    "test_hierarchical_import_deadlock",
    "test_cross_package_circular_import",
]
CP_MEMORY_DIAGNOSTICS = [
    "test_parallel_module_init",
    "test_parallel_meta_path",
    "test_parallel_path_hooks",
    "test_concurrent_futures_circular_import",
    "test_multiprocessing_pool_circular_import",
]
GO_REGRESSIONS = [
    "TestCondSignalDoesNotBlockBehindCanceledWaiters",
    "TestCondCancellationNotification",
]
GO_CONTROLS = [
    "TestMemoryQueue",
    "TestMemoryQueueBlockingCancelled",
    "TestMemoryQueueDrainWhenShutdown",
    "TestAsyncMemoryQueueBlockingCancelled",
    "TestPersistentQueue_FullCapacity",
    "TestPersistentQueue_Shutdown",
    "TestCondSignalAccounting",
]
PG_CONTROLS = ["ddl-dependency-locking", "drop-owned-grant", "alter-domain-validate"]


VS_REGRESSIONS = {
    "$TM_SELECTED_TEXT resolves per edit, not the last selection "
    "(multi-cursor wrap snippet) #206121",
    "apply with multiple cursors threads $CURSOR_NUMBER per edit",
    "$TM_SELECTED_TEXT resolves per edit, not the primary selection #206121",
    "$TM_LINE_NUMBER resolves per edit",
    "per-edit resolution does not corrupt earlier edits when value lengths differ",
    "$CURSOR_NUMBER uses caller-supplied edit order, not range-sorted order",
}


def browser_expectations(source: Path, broken: bool) -> dict[str, str]:
    """Bind every static evaluator test title, including the sole upstream pending test."""
    expected = {}
    pattern = r"^\s*test(?P<skip>\.skip)?\('(?P<title>(?:\\.|[^'\\])*)'"
    for filename in ("snippetSession.test.ts", "snippetController2.test.ts"):
        path = source / "src/vs/editor/contrib/snippet/test/browser" / filename
        for match in re.finditer(pattern, path.read_text(), re.MULTILINE):
            title = match["title"].replace("\\'", "'").replace("\\\\", "\\")
            if title in expected:
                raise ValueError("duplicate browser test title")
            expected[title] = (
                "skip"
                if match["skip"]
                else "fail"
                if broken and title in VS_REGRESSIONS
                else "pass"
            )
    if len(expected) != 86 or len(VS_REGRESSIONS & expected.keys()) != 6:
        raise ValueError("unexpected browser evaluator discovery")
    return expected


def commands(
    case_id: str,
    source: Path,
    state: Path,
    side: str,
    *,
    dependency_only: bool = False,
    discovery_source: Path | None = None,
) -> list[Command]:
    """Describe separate setup and warm tests, using at most two compiler workers."""
    broken = side == "parent"
    result: list[Command] = []
    if case_id == "cpython-import-locks":
        result += [
            Command("configure", [str(source / "configure"), "--with-pydebug"], state),
            Command("build", ["make", "-j2"], state),
            Command(
                "frozen",
                [
                    "/usr/bin/python3",
                    "-c",
                    "import subprocess,sys; from pathlib import Path; "
                    "s,b=map(Path,sys.argv[1:]); "
                    "[subprocess.run([str(b/'Programs/_freeze_module'), n, "
                    "str(s/'Lib/importlib'/f'{f}.py'), "
                    "str(b/'Python/frozen_modules'/f'{o}.h')],check=True) "
                    "for n,f,o in [('importlib._bootstrap','_bootstrap','importlib._bootstrap'),"
                    "('importlib._bootstrap_external','_bootstrap_external','importlib._bootstrap_external')]]",
                    str(source),
                    str(state),
                ],
                state,
            ),
            Command("rebuild", ["make", "-j2"], state),
            Command(
                "runtime",
                [
                    str(state / "python"),
                    "-c",
                    "import sys,sysconfig,importlib._bootstrap as b; "
                    "assert sysconfig.get_config_var('Py_DEBUG') == 1; "
                    f"assert b.__file__ == {str(source / 'Lib/importlib/_bootstrap.py')!r}; "
                    "print(sys.version); print(b.__file__)",
                ],
                state,
            ),
        ]
        for name, tests in [("controls", CP_CONTROLS), ("regressions", CP_REGRESSIONS)]:
            names = [CP_PREFIX + test for test in tests]
            expected = {
                test: "fail" if broken and name == "regressions" else "pass" for test in names
            }
            for attempt in range(3 if name == "regressions" else 1):
                result.append(
                    Command(
                        f"{name}-{attempt + 1}",
                        [str(state / "python"), "-c", PYTHON_RUNNER, *names],
                        state,
                        "test",
                        300,
                        "python",
                        expected,
                    )
                )
        result.append(
            Command(
                "optional-memory-controls",
                [
                    str(state / "python"),
                    "-c",
                    PYTHON_RUNNER,
                    *[CP_PREFIX + name for name in CP_MEMORY_DIAGNOSTICS],
                ],
                state,
                "diagnostic",
                300,
                "python-diagnostic",
            )
        )
    elif case_id == "otel-queue-cancellation":
        module = source / "exporter/exporterhelper"
        result += [
            Command("go-version", ["go", "version"], module),
            Command("dependencies", ["go", "mod", "download", "-json"], module),
            Command(
                "compile-queue",
                [
                    "go",
                    "test",
                    "-c",
                    "-race",
                    "-p=2",
                    "-o",
                    str(state / "queue.test"),
                    "./internal/queue",
                ],
                module,
            ),
        ]
        for name, tests in [("controls", GO_CONTROLS), ("regressions", GO_REGRESSIONS)]:
            # Run individually so a Go synctest deadlock cannot mask other required tests.
            for test in tests:
                for attempt in range(3 if name == "regressions" else 1):
                    result.append(
                        Command(
                            f"{test}-{attempt + 1}",
                            [
                                "go",
                                "test",
                                "-json",
                                "-race",
                                "-p=2",
                                "-count=1",
                                "-timeout=60s",
                                f"-run=^{test}$",
                                "./internal/queue",
                            ],
                            module,
                            "test",
                            600,
                            "go",
                            {test: "fail" if broken and test in GO_REGRESSIONS else "pass"},
                        )
                    )
        if side in ("fixed", "alternative"):
            result.append(
                Command(
                    "full-queue",
                    [
                        "go",
                        "test",
                        "-json",
                        "-race",
                        "-p=2",
                        "-count=1",
                        "-timeout=120s",
                        "./internal/queue",
                    ],
                    module,
                    "diagnostic",
                    600,
                    "go-all",
                )
            )
    elif case_id == "postgres-tablespace-locking":
        prefix = state / "install"
        result += [
            Command(
                "configure",
                [
                    str(source / "configure"),
                    f"--prefix={prefix}",
                    "--enable-cassert",
                    "--enable-debug",
                    "--without-icu",
                    "--without-readline",
                    "--without-zlib",
                ],
                state,
            ),
            Command("build", ["make", "-j2"], state),
            Command("install", ["make", "-j2", "install"], state),
            Command("isolation-build", ["make", "-j2"], state / "src/test/isolation"),
        ]
        for name, tests in [
            ("controls", PG_CONTROLS),
            ("regressions", ["tablespace-dependency-locking"]),
        ]:
            for attempt in range(3 if name == "regressions" else 1):
                run = state / f"{name}-{attempt + 1}"
                result.append(
                    Command(
                        f"{name}-{attempt + 1}",
                        [
                            str(state / "src/test/isolation/pg_isolation_regress"),
                            f"--temp-instance={run}/instance",
                            f"--inputdir={source}/src/test/isolation",
                            f"--outputdir={run}",
                            f"--bindir={prefix}/bin",
                            f"--dlpath={state}/src/test/regress",
                            "--no-locale",
                            *tests,
                        ],
                        state / "src/test/isolation",
                        "test",
                        180,
                        "postgres",
                        {
                            test: "fail" if broken and name == "regressions" else "pass"
                            for test in tests
                        },
                    )
                )
    elif case_id == "vscode-snippet-selections":
        result += [
            Command("node-version", ["node", "--version"], source),
            Command("npm-version", ["npm", "--version"], source),
            Command(
                "dependencies-root",
                ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                source,
            ),
            Command(
                "dependencies-build",
                ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                source / "build",
            ),
            Command(
                "browser",
                ["node", "node_modules/@playwright/test/cli.js", "install", "chromium"],
                source,
            ),
            Command("typecheck", ["npm", "run", "compile-check-ts-native"], source),
            Command("transpile", ["npm", "run", "transpile-client"], source),
            Command(
                "snippet-suites",
                [
                    "node",
                    "test/unit/browser/index.js",
                    "--browser",
                    "chromium",
                    "--reporter",
                    "json",
                    "--run",
                    "src/vs/editor/contrib/snippet/test/browser/snippetSession.test.ts",
                    "--run",
                    "src/vs/editor/contrib/snippet/test/browser/snippetController2.test.ts",
                ],
                source,
                "test",
                300,
                "mocha",
                {} if dependency_only else browser_expectations(discovery_source or source, broken),
            ),
        ]
    else:
        raise ValueError("unknown adapter")
    if side == "partial":
        for command in result:
            if "TestCondCancellationNotification" in command.expected:
                command.expected["TestCondCancellationNotification"] = "fail"
    if dependency_only:
        return [
            command
            for command in result
            if command.name.startswith("dependencies")
            or command.name in {"browser", "go-version", "node-version", "npm-version"}
        ]
    return result


def manifest() -> dict[str, object]:
    """Portable contract independent of local executable/path selection."""
    return {
        "schema_version": 1,
        "platform": "Linux x86_64 (qualification required)",
        "compiler_workers": 2,
        "repetitions": 3,
        "candidate_execution": "requires current runtime and sealed evaluator qualification",
        "cpython": {
            "build": "fresh debug GIL interpreter; frozen importlib regenerated",
            "regressions": CP_REGRESSIONS,
            "controls": CP_CONTROLS,
            "constraint": "upstream scheduler requires _blocking_on and lock name/owner; "
            "lock-lifetime and _resolve_parents diagnostics excluded; no representation "
            "independence or free-threaded coverage claimed",
        },
        "otel": {
            "go": "1.26.0",
            "race": True,
            "regressions": GO_REGRESSIONS,
            "controls": GO_CONTROLS,
            "constraint": "deterministic upstream synctest tests retain "
            "existing L/Wait/Signal condition contract only; waiting counter and "
            "queue lock injection "
            "removed; mock storage controls do not establish crash durability",
        },
        "vscode": {
            "node": "22.22.1",
            "npm": "10.9.4",
            "constraint": "private _snippet backfill test excluded; "
            "six observable regressions and 79 passing checks plus one upstream pending test",
        },
        "postgres": {
            "controls": PG_CONTROLS,
            "schedules": 6,
            "constraint": "dependency errors compare SQLSTATE 2BP01; "
            "prescribed waiting/completion order retained",
        },
    }


if __name__ == "__main__":
    print(json.dumps(manifest(), indent=2))
