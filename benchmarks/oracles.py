"""Trusted objective checks; never import candidate code into the grader process."""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from benchmarks.cases import ROOT, Case
from benchmarks.files import hashes, read_regular, snapshot, write_new_regular
from benchmarks.process import Execution, Executor


@dataclass
class Grade:
    """Objective checks plus explicitly unfinished human assessment."""

    case_id: str
    phase: int
    status: str = "failed"
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    objective_complete: bool = False
    harness_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return JSON evidence, retaining every failure."""
        return asdict(self)


def artifact_hashes(root: Path) -> dict[str, str]:
    """Hash a safely read project snapshot, rejecting aliases and oversized files."""
    return hashes(snapshot(root))


def inspect_archive(path: Path) -> None:
    """Reject archive aliases, traversal, duplicate entries, and decompression bombs."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("archive is not a regular file")
    with zipfile.ZipFile(io.BytesIO(read_regular(path))) as archive:
        names: set[str] = set()
        total = 0
        for entry in archive.infolist():
            name = Path(entry.filename)
            if name.is_absolute() or ".." in name.parts or entry.filename in names:
                raise ValueError("unsafe or duplicate archive member")
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("archive symlink rejected")
            total += entry.file_size
            if total > 20_000_000:
                raise ValueError("archive exceeds decompressed size limit")
            names.add(entry.filename)
        if not {"recordbatch.py", "__main__.py"} <= names:
            raise ValueError("archive lacks required modules")


def seed_upgrade(path: Path) -> None:
    """Create the documented v1 consumer database using trusted SQLite code."""
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.executescript("""
            CREATE TABLE jobs(id INTEGER PRIMARY KEY,tenant TEXT NOT NULL,
                request_id TEXT NOT NULL,payload TEXT NOT NULL,state TEXT NOT NULL,
                UNIQUE(tenant,request_id));
            INSERT INTO jobs VALUES(41,'legacy','retained','{"value":7}','queued');
            PRAGMA user_version=1;
        """)
        data = connection.serialize()
    write_new_regular(path, data)


class Oracle:
    """Compare candidate responses and persistent state outside candidate execution."""

    def __init__(self, root: Path, case: Case, executor: Executor, phase: int = 1) -> None:
        self.root = root.resolve()
        self.consumers: dict[Path, Executor] = {}
        self.case = case
        self.executor = executor
        self.grade = Grade(case.id, phase, needs_review=list(case.review))
        self.phase = phase

    def check(self, condition: bool, label: str) -> None:
        """Record an objective assertion without trusting candidate pass claims."""
        (self.grade.checks if condition else self.grade.failures).append(label)

    def execute(self, argv: list[str], stdin: str = "", cwd: Path | None = None) -> Execution:
        """Execute candidate code only behind the supplied process/isolation boundary."""
        active_root = cwd or self.root
        executor = self.consumers.get(active_root, self.executor)
        result = executor.execute(argv, active_root, stdin=stdin)
        self.grade.commands.append(result.to_dict())
        return result

    def request(
        self,
        data: dict[str, Any],
        db: str = "state.sqlite",
        *,
        expected_exit: int = 0,
        archive: bool = False,
        cwd: Path | None = None,
    ) -> dict[str, Any]:
        """Run the real CLI and decode an untrusted response as data."""
        result = self.execute(
            [
                str(Path(sys.executable).resolve()),
                "recordbatch.pyz" if archive else "recordbatch.py",
                "--db",
                db,
                "request",
                json.dumps(data),
            ],
            cwd=cwd,
        )
        self.check(
            result.returncode == expected_exit and not result.timed_out,
            f"CLI {data['op']} exit {expected_exit}",
        )
        if expected_exit != 0:
            return {}
        value = json.loads(result.stdout)
        validate_response(value, data["op"])
        assert isinstance(value, dict)
        return value

    def script(self, source: str) -> Any:
        """Run an API client in an isolated child, never in the trusted Python process."""
        result = self.execute([str(Path(sys.executable).resolve()), "-B", "-c", source])
        self.check(result.returncode == 0 and not result.timed_out, "API client exits successfully")
        if result.returncode != 0:
            raise ValueError(f"API client failed: {result.stderr[-1000:]}")
        return json.loads(result.stdout)

    def submit(
        self, key: str, tenant: str = "a", payload: dict[str, Any] | None = None, **extra: Any
    ) -> dict[str, Any]:
        """Submit one real CLI request."""
        return self.request(
            {
                "op": "submit",
                "key": key,
                "tenant": tenant,
                "payload": {"value": 1} if payload is None else payload,
                **extra,
            }
        )

    def parallel(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Exercise independent processes without imposing a lock-strategy-specific barrier."""
        with ThreadPoolExecutor(max_workers=len(requests)) as pool:
            return list(pool.map(self.request, requests))

    def sql(self, statement: str) -> list[tuple[Any, ...]]:
        """Query a main/WAL snapshot in a bounded isolated process, never in the grader."""
        names = ("state.sqlite", "state.sqlite-wal", "state.sqlite-journal")
        files: dict[str, bytes] = {}
        for name in names:
            try:
                files[name] = read_regular(self.root / name)
            except FileNotFoundError:
                if name == "state.sqlite":
                    raise
        if sum(map(len, files.values())) > 20_000_000:
            raise ValueError("database snapshot exceeds size limit")
        # Candidate commands have terminated. Also reject an externally changing snapshot
        # rather than mixing a checkpointed main file with an incompatible WAL generation.
        for name in names:
            try:
                current = read_regular(self.root / name)
            except FileNotFoundError:
                current = None
            if current != files.get(name):
                raise ValueError("database changed while snapshotting")
        directory = Path(tempfile.mkdtemp(prefix="benchmark-sql-", dir=self.root.parent))
        workspace = directory / "snapshot"
        workspace.mkdir()
        for name, data in files.items():
            write_new_regular(workspace / name, data)
        executor = self.executor.for_workspace(workspace)
        result = executor.execute(
            [str(Path(sys.executable).resolve()), "-I", "-B", "-c", SQL_INSPECTION],
            workspace,
            stdin=json.dumps({"statement": statement}),
            timeout=5,
        )
        self.grade.commands.append(result.to_dict())
        if result.returncode != 0 or result.timed_out or result.output_limited:
            raise ValueError(f"bounded database inspection failed: {result.stderr[-500:]}")
        value = json.loads(result.stdout)
        rows = value.get("rows") if isinstance(value, dict) else None
        if (
            not isinstance(rows, list)
            or len(rows) > 1000
            or any(not isinstance(row, list) for row in rows)
        ):
            raise ValueError("invalid database inspection result")
        return [tuple(row) for row in rows]

    def identity(self) -> None:
        """Check tenant/request/payload identity and positive independent controls."""
        payload = {"a": 1, "b": 2}
        first = self.submit("same", payload=payload)
        repeat = self.submit("same", payload={"b": 2, "a": 1})
        other = self.submit("same", "b")
        self.check(first.get("ok") is True and first == repeat, "same identity returns same job")
        self.check(
            other.get("ok") is True
            and other["job"]["tenant"] == "b"
            and other["job"]["id"] != first["job"]["id"],
            "tenant keys are independent",
        )
        self.check(
            self.submit("same", payload={"value": 2}).get("error") == "conflict",
            "different payload conflicts",
        )
        self.request({"op": "complete", "tenant": "a", "id": first["job"]["id"]})
        separate = self.submit("different", payload=payload)
        self.check(
            separate.get("ok") is True and separate["job"]["id"] != first["job"]["id"],
            "same payload with different identity creates separate job",
        )
        self.check(
            self.submit("denied", principal="b").get("error") == "forbidden", "authorization"
        )

    def admission(self) -> None:
        """Check concurrent admissions and rollback after insertion failure."""
        self.request({"op": "init"})
        results = self.parallel(
            [
                {"op": "submit", "tenant": "a", "key": str(index), "payload": {}}
                for index in range(8)
            ]
        )
        self.check(
            sum(result.get("ok") is True for result in results) == 1,
            "eight independent processes admit exactly one",
        )
        self.check(
            self.sql("SELECT count(*) FROM jobs WHERE tenant='a'") == [(1,)],
            "one persistent admitted job",
        )
        self.check(
            self.submit("broken", "rollback", fault="insert").get("error") == "storage",
            "insertion failure is explicit",
        )
        self.check(
            self.submit("works", "rollback").get("ok") is True,
            "failed insert releases reservation atomically",
        )
        self.check(
            self.submit("independent", "other").get("ok") is True,
            "independent tenant success control",
        )

    def effects(self) -> None:
        """Check real process exits, duplicate concurrency, and acknowledged replay."""
        self.request({"op": "init"})
        for fault in ("before_commit", "after_commit"):
            event = {"op": "effect", "tenant": "a", "event_id": fault, "delta": 3}
            self.request({**event, "fault": fault}, expected_exit=75)
            self.request(event)
        duplicate = {"op": "effect", "tenant": "a", "event_id": "dupe", "delta": 5}
        self.parallel([duplicate] * 6)
        self.request({"op": "ack", "tenant": "a", "event_id": "dupe"})
        self.request({"op": "cleanup", "tenant": "a"})
        replay = self.request(duplicate)
        self.check(replay.get("value") == 11, "replay after ack and cleanup has no second effect")
        distinct = self.request({**duplicate, "event_id": "distinct"})
        self.check(distinct.get("value") == 16, "same delta distinct identity applies")
        self.check(
            self.sql("SELECT value FROM balances WHERE tenant='a'") == [(16,)],
            "persistent aggregate matches externally counted effects",
        )
        isolated = self.request({**duplicate, "tenant": "b"})
        self.check(isolated.get("value") == 5, "effect identity is tenant scoped")

    def deletion(self) -> None:
        """Separate absence, authorization denial, and real SQLite failure."""
        first = self.submit("first")
        job_id = first["job"]["id"]
        data = {"op": "delete", "tenant": "a", "id": job_id}
        self.check(self.request(data) == {"ok": True}, "existing deletion")
        self.check(
            self.sql("SELECT count(*) FROM jobs WHERE tenant='a'") == [(0,)],
            "deleted job is persistently absent",
        )
        self.check(
            self.sql("SELECT used FROM capacity WHERE tenant='a'") == [(0,)],
            "deletion releases capacity",
        )
        self.check(self.request(data) == {"ok": True}, "already absent deletion")
        self.check(
            self.request({**data, "principal": "other"}).get("error") == "forbidden",
            "authorization remains effective for absent objects",
        )
        value = self.script("""import json, sqlite3
from recordbatch import Store
store=Store('broken.sqlite','a')
with sqlite3.connect('broken.sqlite') as connection:
    connection.execute('DROP TABLE jobs')
try:
    store.delete('a',999)
except sqlite3.Error:
    result='storage'
else:
    result='swallowed'
print(json.dumps(result))
""")
        self.check(value == "storage", "real storage failure propagates")
        replacement = self.submit("replacement")
        self.check(replacement.get("ok") is True, "new admission after deletion")
        listed = self.request({"op": "status", "tenant": "a"})
        self.check(
            listed.get("jobs") == [replacement.get("job")],
            "only replacement remains after deletion",
        )

    def batch(self) -> None:
        """Exercise one-shot generators, ordered mixed results, and API authorization."""
        value = self.script("""import json
from recordbatch import Store
store=Store('state.sqlite','a')
empty=store.submit_many('a',iter(()))
items=({'key':key,'payload':{'value':value}} for key,value in [('x',1),('x',1),('x',2),('y',1)])
results=store.submit_many('a',items)
try:
    store.submit_many('b',iter(()))
except PermissionError:
    denied=True
else:
    denied=False
print(json.dumps({'empty':empty,'results':results,'denied':denied}))
""")
        self.check(value["empty"] == [], "empty iterable")
        results = value["results"]
        self.check(
            len(results) == 4
            and results[0] == results[1]
            and results[0]["ok"] is True
            and [item.get("error") for item in results[2:]] == ["conflict", "capacity"],
            "one-shot iterable gives ordered mixed results",
        )
        self.check(value["denied"] is True, "batch authorizes even empty iterables")
        self.check(self.submit("x").get("ok") is True, "legacy submit compatibility")
        storage = self.script("""import json,sqlite3
from recordbatch import Store
store=Store('storage.sqlite','a')
with sqlite3.connect('storage.sqlite') as connection:
    connection.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON jobs "
                       "WHEN NEW.request_id='broken' BEGIN SELECT RAISE(ABORT,'failure'); END")
results=store.submit_many('a',({'key':key,'payload':{}} for key in ['broken','valid']))
print(json.dumps(results))
""")
        self.check(
            storage[0] == {"ok": False, "error": "storage"} and storage[1].get("ok") is True,
            "batch continues after real insertion failure without leaking capacity",
        )

    def adapters(self) -> None:
        """Compare client-visible representations without prescribing implementation structure."""
        jobs = [
            {
                "id": 7,
                "tenant": "a",
                "key": 'comma,quote"\nline',
                "state": "queued",
                "payload": {"x": 1},
            }
        ]
        source = (
            "import json\nfrom recordbatch import render\n"
            f"jobs=json.loads({json.dumps(json.dumps(jobs))})\n"
            "result={'json':render(jobs),'csv':render(jobs,'csv'),'empty':render([],'csv')}\n"
            "try:\n    render(jobs,'bogus')\nexcept ValueError as error:\n"
            "    result['error']=str(error)\nprint(json.dumps(result))\n"
        )
        value = self.script(source)
        self.check(value["json"] == json.dumps(jobs, sort_keys=True), "JSON bytes preserved")
        self.check(
            list(csv.reader(io.StringIO(value["csv"])))
            == [["id", "tenant", "key", "state"], ["7", "a", jobs[0]["key"], "queued"]],
            "CSV quoting and output contract",
        )
        self.check(
            list(csv.reader(io.StringIO(value["empty"]))) == [["id", "tenant", "key", "state"]],
            "empty CSV header",
        )
        self.check(value.get("error") == "unknown_adapter", "unknown adapter remains explicit")
        if self.phase == 2:
            value = self.script("""import json
from recordbatch import render
nested={'identity':{'id':7,'tenant':'a','key':'k'},'status':'queued','data':{'x':1}}
result={name:render((row for row in [nested]),name) for name in ['json','csv','ndjson']}
result['empty']=render(iter(()),'ndjson')
print(json.dumps(result))
""")
            canonical = {"id": 7, "tenant": "a", "key": "k", "state": "queued", "payload": {"x": 1}}
            self.check(
                json.loads(value["ndjson"]) == canonical and value["ndjson"].endswith("\n"),
                "sequel ndjson new representation",
            )
            self.check(
                json.loads(value["json"]) == [canonical] and value["empty"] == "",
                "sequel generator and empty compatibility",
            )
            self.check(
                list(csv.reader(io.StringIO(value["csv"])))[1] == ["7", "a", "k", "queued"],
                "sequel CSV new representation",
            )

    def status_filter(self) -> None:
        """Check scoping, old callers, supported states and invalid state errors."""
        first = self.submit("a")
        self.request({"op": "complete", "tenant": "a", "id": first["job"]["id"]})
        self.submit("b")
        self.submit("other", "b")
        all_jobs = self.request({"op": "status", "tenant": "a"})["jobs"]
        filtered = self.request({"op": "status", "tenant": "a", "state": "completed"})["jobs"]
        self.check(
            len(all_jobs) == 2 and all(job["tenant"] == "a" for job in all_jobs), "legacy scope"
        )
        self.check(filtered == [all_jobs[0]], "status filter applies inside tenant")
        self.check(
            self.request({"op": "status", "tenant": "a", "state": "bogus"}).get("error")
            == "invalid_state",
            "invalid state is explicit",
        )

    def transitions(self) -> None:
        """Exercise races, rollback, repeated operations, and restarted capacity use."""
        first = self.submit("first")
        job_id = first["job"]["id"]
        base = {"tenant": "a", "id": job_id}
        failed = self.request({**base, "op": "cancel", "fault": "transition"})
        self.check(failed.get("error") == "storage", "transition failure explicit")
        self.check(self.submit("blocked").get("error") == "capacity", "rollback keeps slot owned")
        self.parallel([{**base, "op": op} for op in ("cancel", "complete", "cancel", "complete")])
        state = self.request({"op": "status", "tenant": "a"})["jobs"][0]["state"]
        self.check(state in {"completed", "cancelled"}, "one terminal race winner")
        for operation in ("cancel", "complete", "cancel"):
            response = self.request({**base, "op": operation})
            self.check(response["job"]["state"] == state, "terminal state not overwritten")
        self.check(
            self.sql("SELECT used FROM capacity WHERE tenant='a'") == [(0,)],
            "capacity released exactly once",
        )
        second = self.submit("second")
        self.check(second.get("ok") is True, "new work succeeds after release")
        self.check(
            self.submit("third").get("error") == "capacity", "capacity cannot drift negative"
        )
        self.request({"op": "cancel", "tenant": "a", "id": second["job"]["id"]})
        resumed = self.request({"op": "resume", "tenant": "a", "id": second["job"]["id"]})
        self.check(resumed["job"]["state"] == "queued", "cancelled work resumes across processes")
        self.check(self.submit("fourth").get("error") == "capacity", "resume reserves slot")
        self.request({"op": "complete", "tenant": "a", "id": second["job"]["id"]})
        self.check(
            self.request({"op": "resume", "tenant": "a", "id": second["job"]["id"]}).get("error")
            == "completed",
            "completed work cannot resume",
        )
        self.package()

    def delivery(self) -> None:
        """Probe identical timeout observations with distinct external effect histories."""
        value = self.script("""import json
from recordbatch import Store
results={}
for name,effect in [('before',False),('after',True)]:
    store=Store(name+'.sqlite','a')
    calls=[]
    effects=[]
    def provider():
        calls.append('call')
        if effect:
            effects.append('effect')
        raise TimeoutError('ambiguous timeout')
    first=store.deliver('a','same',provider)
    restarted=Store(name+'.sqlite','a').deliver('a','same',provider)
    results[name]={'first':first,'restarted':restarted,'calls':len(calls),'effects':len(effects)}
store=Store('normal.sqlite','a')
calls=[]
def success():
    calls.append('effect')
results['success']=[store.deliver('a','ok',success),store.deliver('a','ok',success),len(calls)]
def reject():
    raise ValueError('known-before-effect rejection')
results['rejection']=[store.deliver('a','retry',reject),store.deliver('a','retry',success)]
try:
    store.deliver('b','no',success)
except PermissionError:
    results['denied']=True
else:
    results['denied']=False
print(json.dumps(results))
""")
        for name, effects in (("before", 0), ("after", 1)):
            self.check(
                value[name]
                == {"first": "unknown", "restarted": "unknown", "calls": 1, "effects": effects},
                f"{name}-effect timeout remains unknown",
            )
        self.check(
            value["success"] == ["delivered", "delivered", 1], "successful ack positive control"
        )
        self.check(value["rejection"] == ["rejected", "delivered"], "known rejection may retry")
        self.check(value["denied"] is True, "delivery authorization")
        # True exit inside the provider after the durable fence, then a fresh process.
        result = self.execute(
            [
                str(Path(sys.executable).resolve()),
                "-c",
                "from recordbatch import Store; import os; "
                "Store('crash.sqlite','a').deliver('a','x',lambda:os._exit(75))",
            ]
        )
        self.check(result.returncode == 75, "actual exit during external attempt")
        restarted = self.script(
            "from recordbatch import Store; import json; "
            "print(json.dumps(Store('crash.sqlite','a').deliver('a','x',"
            "lambda:None)))"
        )
        self.check(restarted == "unknown", "crashed external attempt is not blindly retried")
        self.request({"op": "init"})
        concurrent_source = """import json
from recordbatch import Store
store=Store('delivery-concurrent.sqlite','a')
def provider():
    with open('provider-effects.log','a') as output:
        output.write('effect\\n')
print(json.dumps(store.deliver('a','one',provider)))
"""
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [
                pool.submit(
                    self.execute, [str(Path(sys.executable).resolve()), "-c", concurrent_source]
                )
                for _ in range(6)
            ]
            responses = [future.result() for future in futures]
        self.check(
            all(response.returncode == 0 for response in responses),
            "concurrent delivery processes finish",
        )
        self.check(
            read_regular(self.root / "provider-effects.log").decode().splitlines() == ["effect"],
            "concurrent duplicate delivery calls provider once",
        )
        self.package()

    def package(self) -> None:
        """Build and invoke only the archive in a fresh consumer directory."""
        result = self.execute([str(Path(sys.executable).resolve()), "build.py"])
        self.check(result.returncode == 0, "archive builds")
        inspect_archive(self.root / "recordbatch.pyz")
        consumer = self.new_consumer()
        response = self.request(
            {"op": "submit", "key": "archive", "payload": {}}, archive=True, cwd=consumer
        )
        self.check(response.get("ok") is True, "archive-only fresh consumer")

    def new_consumer(self) -> Path:
        """Stage archive bytes outside every previously candidate-writable directory."""
        archive = read_regular(self.root / "recordbatch.pyz")
        directory = Path(tempfile.mkdtemp(prefix="benchmark-consumer-", dir=self.root.parent))
        consumer = directory / "project"
        consumer.mkdir()
        (consumer / "recordbatch.pyz").write_bytes(archive)
        seed_upgrade(consumer / "upgrade.sqlite")
        self.consumers[consumer] = self.executor.for_workspace(consumer)
        return consumer

    def documentation(self) -> None:
        """Execute structured documented commands against immutable real application code."""
        for name in ("recordbatch.py", "build.py"):
            self.check(
                read_regular(self.root / name) == (ROOT / "recordbatch" / name).read_bytes(),
                f"immutable documentation source: {name}",
            )
        blocks = re.findall(
            r"```recordbatch\s*\n(.*?)\n```", read_regular(self.root / "README.md").decode(), re.S
        )
        self.check(bool(blocks), "documented executable procedure exists")
        observed: list[dict[str, Any]] = []
        seed_upgrade(self.root / "upgrade.sqlite")
        consumer: Path | None = None
        for block in blocks:
            steps = json.loads(block)["steps"]
            if not isinstance(steps, list) or not steps:
                raise ValueError("documentation steps must be a nonempty list")
            for step in steps:
                argv = step["argv"]
                if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
                    raise ValueError("documentation argv must contain strings")
                if argv == ["python", "build.py"]:
                    result = self.execute([str(Path(sys.executable).resolve()), "build.py"])
                    self.check(result.returncode == step.get("expect_exit", 0), "documented build")
                    inspect_archive(self.root / "recordbatch.pyz")
                    consumer = self.new_consumer()
                    continue
                if (
                    len(argv) != 6
                    or argv[0] != "python"
                    or argv[1] not in {"recordbatch.py", "recordbatch.pyz"}
                    or argv[2] != "--db"
                    or argv[4] != "request"
                    or Path(argv[3]).name != argv[3]
                    or not argv[3].endswith(".sqlite")
                ):
                    raise ValueError("documented command violates the public example contract")
                cwd = consumer if argv[1].endswith(".pyz") else self.root
                if cwd is None:
                    raise ValueError("archive must be built before consumer examples")
                result = self.execute([str(Path(sys.executable).resolve()), *argv[1:]], cwd=cwd)
                self.check(
                    result.returncode == step.get("expect_exit", 0), "documented command exit"
                )
                response = json.loads(result.stdout)
                validate_response(response)
                self.check(
                    matches(response, step["expect"], step.get("subset", False)),
                    "documented expected result matches real command",
                )
                try:
                    request = json.loads(argv[5])
                except json.JSONDecodeError:
                    request = {"op": "invalid_json"}
                observed.append(
                    {
                        "request": request,
                        "response": response,
                        "archive": cwd == consumer,
                        "exit": result.returncode,
                        "db": argv[3],
                        "database": str(cwd / argv[3]),
                    }
                )
        if self.case.id != "docs-hard":
            accepted = [
                item
                for item in observed
                if item["request"].get("op") == "submit"
                and item["response"].get("ok") is True
                and isinstance(item["response"].get("job"), dict)
                and item["response"]["job"].get("state") == "queued"
            ]
            self.check(bool(accepted), "documented successful queued acceptance")
            self.check(
                any(
                    status["request"].get("op") == "status"
                    and status["response"].get("ok") is True
                    and status["db"] == submit["db"]
                    and submit["response"]["job"] in status["response"].get("jobs", [])
                    for submit in accepted
                    for status in observed
                ),
                "documented status confirms the accepted queued job",
            )
        required = {"init", "submit", "status"}
        if self.case.id == "docs-medium":
            required |= {"complete"}
            for error in ("conflict", "capacity", "forbidden"):
                self.check(
                    any(item["response"].get("error") == error for item in observed),
                    f"documented {error} response exercised",
                )
            self.check(
                any(
                    item["response"].get("job", {}).get("state") == "completed" for item in observed
                ),
                "documented completion exercised",
            )
            self.check(
                identical_retry(observed),
                "documented retry exercised",
            )
        if self.case.id == "docs-hard":
            required = {"invalid_json", "init", "submit", "status"}
            self.check(
                bool(observed) and all(item["archive"] for item in observed),
                "consumer executes archive alone",
            )
            self.check(
                any(
                    item["db"] == "upgrade.sqlite"
                    and item["response"].get("jobs")
                    == [
                        {
                            "id": 41,
                            "tenant": "legacy",
                            "key": "retained",
                            "payload": {"value": 7},
                            "state": "queued",
                        }
                    ]
                    for item in observed
                ),
                "upgrade preserves seeded state",
            )
            self.check(
                any(item["exit"] == 2 for item in observed), "failure and recovery exercised"
            )
        self.check(
            required <= {item["request"].get("op") for item in observed},
            "required documented operations exercised",
        )

    def run(self) -> Grade:
        """Grade all requirements available to deterministic objective checks."""
        try:
            self.grade.artifacts = artifact_hashes(self.root)
            operations = {
                "ddia-easy": self.identity,
                "ddia-medium": self.admission,
                "ddia-hard": self.effects,
                "design-easy": self.deletion,
                "design-medium": self.batch,
                "design-hard": self.adapters,
                "integrated-easy": self.status_filter,
                "integrated-medium": self.transitions,
                "integrated-hard": self.delivery,
            }
            if self.case.family == "docs":
                self.documentation()
            else:
                operations[self.case.id]()
            final_hashes = artifact_hashes(self.root)
            for name, original in self.grade.artifacts.items():
                if Path(name).suffix in {".py", ".md", ".toml"}:
                    self.check(
                        final_hashes.get(name) == original,
                        f"source unchanged during grading: {name}",
                    )
            self.grade.objective_complete = True
        except (
            IndexError,
            AttributeError,
            RecursionError,
            ValueError,
            KeyError,
            TypeError,
            OSError,
            sqlite3.Error,
            zipfile.BadZipFile,
        ) as error:
            self.grade.failures.append(
                f"oracle could not complete: {type(error).__name__}: {error}"
            )
        except Exception as error:
            self.grade.harness_error = f"{type(error).__name__}: {error}"
            self.grade.failures.append("unexpected harness error")
        self.grade.status = (
            "harness_error"
            if self.grade.harness_error
            else "failed"
            if self.grade.failures
            else "needs_review"
            if self.grade.needs_review
            else "passed"
        )
        return self.grade


def matches(actual: Any, expected: Any, subset: bool) -> bool:
    """Compare documented data, supporting explicitly requested object subsets."""
    if subset and isinstance(expected, dict) and isinstance(actual, dict):
        return all(
            key in actual and matches(actual[key], value, subset) for key, value in expected.items()
        )
    return bool(actual == expected)


def validate_response(value: Any, operation: str | None = None) -> None:
    """Reject malformed public result shapes before oracle indexing or iteration."""
    if not isinstance(value, dict) or type(value.get("ok")) is not bool:
        raise ValueError("response must be an object with boolean ok")
    if not value["ok"]:
        if not isinstance(value.get("error"), str):
            raise ValueError("failed response must contain an error string")
        return
    if operation in {"submit", "cancel", "complete", "resume"}:
        job = value.get("job")
        if not isinstance(job, dict) or not isinstance(job.get("id"), int):
            raise ValueError("successful operation requires a job with integer id")
    if operation == "status":
        jobs = value.get("jobs")
        if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
            raise ValueError("successful status requires a list of job objects")


SQL_INSPECTION = r"""
import json, sqlite3, sys, time
try:
    request = json.load(sys.stdin)
    deadline = time.monotonic() + 0.5
    calls = 0
    def progress():
        global calls
        calls += 1
        return int(calls >= 1000 or time.monotonic() >= deadline)
    # The directory is a fresh snapshot, including committed WAL frames. Do not use
    # immutable=1 or deserialize(main): both would discard required WAL semantics.
    connection = sqlite3.connect('file:state.sqlite?mode=ro', uri=True, timeout=0.5)
    connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
    connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 10_000)
    connection.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 100)
    connection.set_progress_handler(progress, 1000)
    connection.execute('PRAGMA query_only=ON')
    connection.execute('PRAGMA trusted_schema=OFF')
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
               sqlite3.SQLITE_RECURSIVE}
    connection.set_authorizer(lambda operation, *_: sqlite3.SQLITE_OK
                              if operation in allowed else sqlite3.SQLITE_DENY)
    cursor = connection.execute(request['statement'])
    rows = []
    row_bytes = 0
    for row in cursor:
        row_bytes += len(json.dumps(row).encode())
        if len(rows) >= 1000 or row_bytes > 1_000_000:
            raise ValueError('row/output limit exceeded')
        rows.append(row)
    encoded = json.dumps({'rows': rows})
    if len(encoded.encode()) > 1_000_000:
        raise ValueError('output limit exceeded')
    connection.close()
    print(encoded)
except (sqlite3.Error, ValueError, TypeError, KeyError, MemoryError) as error:
    print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
    raise SystemExit(2)
"""


def identical_retry(observed: list[dict[str, Any]]) -> bool:
    """Require a repeated request identity/payload and stable logical job in the same DB."""
    seen: dict[tuple[str, str, str, str], tuple[Any, ...]] = {}
    for item in observed:
        request, response = item["request"], item["response"]
        job = response.get("job")
        if (
            request.get("op") != "submit"
            or response.get("ok") is not True
            or not isinstance(job, dict)
            or not isinstance(request.get("payload"), dict)
        ):
            continue
        payload = json.dumps(request["payload"], sort_keys=True, separators=(",", ":"))
        key = (item["database"], request.get("tenant", "demo"), request["key"], payload)
        logical_job = (
            job.get("id"),
            job.get("tenant"),
            job.get("key"),
            json.dumps(job.get("payload"), sort_keys=True, separators=(",", ":")),
        )
        if logical_job[1:] != (key[1], key[2], payload) or not isinstance(logical_job[0], int):
            continue
        if key in seen and seen[key] == logical_job:
            return True
        seen[key] = logical_job
    return False
