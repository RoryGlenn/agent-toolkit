"""Executable model-free resource, deadline, cleanup and native runtime controls."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from benchmarks.large_projects.deadline import supervise
from benchmarks.large_projects.native import package_identity, preflight
from benchmarks.large_projects.prepare import git
from benchmarks.large_projects.resources import (
    Deadline,
    Limits,
    ResourceCell,
    cleanup_owned,
    require,
)
from benchmarks.large_projects.runner import harness_hashes, write_json
from benchmarks.runtime import config_text, stage_runtime

GATES = {
    "filesystem_quotas",
    "aggregate_memory",
    "aggregate_pids",
    "nested_tmpfs",
    "staging_deadline",
    "cancellation_cleanup",
    "success_failure_cleanup",
    "frozen_artifact",
    "native_tools",
    "descendant_budget",
}


def kernel_controls(root: Path, owner: str, deadline: Deadline) -> dict[str, Any]:
    """Exercise real ENOSPC, forked OOM, pid exhaustion, nested mounts and freeze behavior."""
    root.mkdir(parents=True, exist_ok=False)
    result: dict[str, Any] = {}
    limits = Limits(memory_bytes=64 * 1024**2, filesystem_bytes=64 * 1024**2, pids=24)
    with ResourceCell(root / "quota", limits, owner=owner, deadline=deadline) as cell:
        script = r"""import errno,json,pathlib,sys
roots=[pathlib.Path(sys.argv[1]),pathlib.Path('/tmp'),pathlib.Path('/dev/shm')]
checks={}
for p in roots:
 f=p/'fill';size=0
 try:
  with f.open('wb',buffering=0) as out:
   while True: size+=out.write(b'x'*65536)
 except OSError as e:
  assert e.errno==errno.ENOSPC,(str(p),e)
 finally:f.unlink(missing_ok=True)
 checks[str(p)]={'allocated_before_ENOSPC':size}
for p in ['/usr/bin/.toolkit-canary','/etc/hosts','/dev/new-file','/sys/fs/cgroup/memory.max']:
 try:open(p,'wb').write(b'bad')
 except OSError as e:assert e.errno in (13,30),(p,e)
 else:raise AssertionError('unbounded writable data path: '+p)
print(json.dumps(checks))
"""
        executed = require(
            cell.execute(["/usr/bin/python3", "-I", "-B", "-c", script, str(cell.root)])
        )
        result["filesystem_quotas"] = {
            "status": "passed",
            "execution": executed.to_dict(),
            "kernel": cell.enforcement,
        }
        pids = r"""import os,time,signal,json,errno
children=[]
try:
 for _ in range(100):
  try:pid=os.fork()
  except OSError as e:
   assert e.errno==errno.EAGAIN;print(json.dumps({'forked':len(children),'errno':e.errno}));break
  if pid==0:time.sleep(20);os._exit(0)
  children.append(pid)
 else:raise AssertionError('pid ceiling not enforced')
 assert 5<=len(children)<24
finally:
 for pid in children:
  try:os.kill(pid,signal.SIGKILL)
  except ProcessLookupError:pass
 for pid in children:os.waitpid(pid,0)
"""
        result["aggregate_pids"] = {
            "status": "passed",
            "execution": require(
                cell.execute(["/usr/bin/python3", "-I", "-B", "-c", pids])
            ).to_dict(),
        }
        # Each process's 20MiB allocation fits individually; their shared cgroup cannot.
        memory = r"""import os,time
children=[]
for _ in range(5):
 pid=os.fork()
 if pid==0:
  data=bytearray(20*1024**2)
  for i in range(0,len(data),4096):data[i]=1
  time.sleep(2);os._exit(0)
 children.append(pid)
for pid in children:os.waitpid(pid,0)
"""
        executed = cell.execute(["/usr/bin/python3", "-I", "-B", "-c", memory], timeout=15)
        events = cell.events()
        if not events["oom_kill"]:
            raise ValueError("forked aggregate memory control did not reach kernel OOM enforcement")
        result["aggregate_memory"] = {
            "status": "passed",
            "execution": executed.to_dict(),
            "events": events,
        }
    nested_limits = Limits(memory_bytes=128 * 1024**2, filesystem_bytes=128 * 1024**2)
    with ResourceCell(
        root / "nested", nested_limits, owner=owner, deadline=deadline, native_sandbox=True
    ) as cell:
        script = r"""import ctypes,os,pathlib,sys
libc=ctypes.CDLL(None,use_errno=True);uid,gid=os.getuid(),os.getgid()
assert libc.unshare(0x10000000|0x00020000)==0,ctypes.get_errno()
pathlib.Path('/proc/self/setgroups').write_text('deny')
pathlib.Path('/proc/self/uid_map').write_text(f'0 {uid} 1')
pathlib.Path('/proc/self/gid_map').write_text(f'0 {gid} 1')
p=pathlib.Path(sys.argv[1])/'extra';p.mkdir()
assert libc.mount(b'tmpfs',os.fsencode(p),b'tmpfs',0,b'size=1073741824')==0,ctypes.get_errno()
with (p/'fill').open('wb',buffering=0) as out:
 for _ in range(512):out.write(b'x'*1024**2)
raise AssertionError('nested tmpfs bypassed the global backing-page bound')
"""
        executed = cell.execute(
            ["/usr/bin/python3", "-I", "-B", "-c", script, str(cell.root)], timeout=20
        )
        events = cell.events()
        passed = executed.returncode == 137 and events["oom_kill"] >= 1
        nested = {
            "status": "passed" if passed else "failed",
            "execution": executed.to_dict(),
            "events": events,
        }
        write_json(root / "nested-tmpfs.json", nested)
        if not passed:
            raise ValueError(
                "nested allocated-storage control did not hit its memory cgroup: "
                f"returncode={executed.returncode}, memory.events={events}, "
                f"stderr={executed.stderr[-2000:]!r}; see nested-tmpfs.json"
            )
        result["nested_tmpfs"] = nested
    # A private named tmpfs volume must expose stable nonempty bytes while *paused*.
    with ResourceCell(root / "freeze", limits, owner=owner, deadline=deadline) as cell:
        require(
            cell.execute(
                [
                    "/bin/sh",
                    "-c",
                    "mkdir workspace; echo positive > workspace/file; "
                    "(while true; do echo tick >> workspace/log; sleep .05; done) "
                    ">/dev/null 2>&1 </dev/null &",
                ],
                cell.root,
            )
        )
        cell.freeze()
        first, second = root / "first.tar", root / "second.tar"
        cell.download(cell.root / "workspace", first)
        cell.download(cell.root / "workspace", second)
        import tarfile

        def entries(path: Path) -> dict[str, bytes]:
            with tarfile.open(path) as archive:
                entries = {}
                for member in archive.getmembers():
                    if member.isfile():
                        stream = archive.extractfile(member)
                        if stream is None:
                            raise ValueError("missing frozen positive artifact")
                        entries[member.name] = stream.read()
                return entries

        actual = entries(first)
        if actual != entries(second) or actual.get("workspace/file") != b"positive\n":
            raise ValueError("paused artifact snapshot is empty or still changing")
        result["frozen_artifact"] = {"status": "passed", "files": sorted(actual)}
    # Both ordinary return and raised failure remove detached session/process descendants.
    for fail in (False, True):
        try:
            with ResourceCell(
                root / f"lifecycle-{fail}", limits, owner=owner, deadline=deadline
            ) as cell:
                require(
                    cell.execute(
                        [
                            "/usr/bin/python3",
                            "-c",
                            "import os,time\n"
                            "if os.fork()==0:\n"
                            " os.setsid(); fd=os.open('/dev/null',os.O_RDWR)\n"
                            " [os.dup2(fd,i) for i in range(3)]; time.sleep(60)\n",
                        ]
                    )
                )
                if fail:
                    raise RuntimeError("expected lifecycle failure")
        except RuntimeError as exc:
            if not fail or str(exc) != "expected lifecycle failure":
                raise
    cleanup = cleanup_owned(owner)
    if not cleanup["complete"] or cleanup["removed"]:
        raise ValueError("normal/failure cleanup leaked an owned container or volume")
    result["success_failure_cleanup"] = {"status": "passed", "cleanup": cleanup}
    return result


def watchdog_controls(root: Path) -> dict[str, Any]:
    """The watchdog must interrupt blocked staging before any candidate has started."""

    def blocked(deadline: Deadline, owner: str) -> dict[str, Any]:
        with ResourceCell(
            root / "blocked-cell", Limits(seconds=20), owner=owner, deadline=deadline
        ):
            time.sleep(20)
        return {"status": "incorrectly_completed"}

    timed = supervise(root / "timeout", 1, blocked)
    if timed["status"] != "timed_out" or not timed["cleanup"]["complete"]:
        raise ValueError("staging-inclusive timeout/cleanup control failed")
    sender = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import os,sys,time,signal; time.sleep(1); os.kill(int(sys.argv[1]),signal.SIGINT)",
            str(os.getpid()),
        ],
        env={},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        cancelled = supervise(root / "cancel", 15, blocked)
    finally:
        if sender.poll() is None:
            sender.kill()
        sender.wait(timeout=5)
    if cancelled["status"] != "cancelled" or not cancelled["cleanup"]["complete"]:
        raise ValueError("external cancellation/cleanup control failed")
    return {
        "staging_deadline": {"status": "passed", "evidence": timed},
        "cancellation_cleanup": {"status": "passed", "evidence": cancelled},
    }


def qualify_runtime(codex: Path, output: Path, seconds: int = 240) -> dict[str, Any]:
    """No missing, skipped or unexecuted control can establish runtime readiness."""
    initial = harness_hashes()

    def work(deadline: Deadline, owner: str) -> dict[str, Any]:
        controls = kernel_controls(output / "resources", owner, deadline)
        controls.update(watchdog_controls(output / "watchdogs"))
        stage = output / "native-cell"
        stage.mkdir()
        for name in ("workspace", "actor-home", "client-home", "private-tmp"):
            (stage / name).mkdir()
        stage_runtime(stage / "actor-home")
        (stage / "client-home/config.toml").write_text(
            config_text(
                stage / "workspace",
                stage / "actor-home",
                stage / "client-home",
                stage / "private-tmp",
                "unused",
                "low",
                1000,
                local_network=True,
            )
        )
        positive = output / "host-positive"
        positive.write_text("outside-positive")
        objects = output / "outside-git"
        objects.mkdir()
        git(objects, "init", "--bare", "--template=")
        oid = git(objects, "hash-object", "-w", str(positive)).decode().strip()
        limits = Limits(memory_bytes=1024**3, filesystem_bytes=1024**3, seconds=seconds)
        with ResourceCell(
            stage,
            limits,
            owner=owner,
            deadline=deadline,
            native_sandbox=True,
            client_transport=True,
            readonly=[codex.parent.parent],
        ) as cell:
            for name in ("workspace", "actor-home", "client-home", "private-tmp"):
                cell.upload(stage / name, stage / name)
            version = require(cell.execute([str(codex), "--version"]))
            if version.stdout.strip() != "codex-cli 0.165.0":
                raise ValueError(
                    "runtime qualification requires the full Codex CLI 0.165.0 package"
                )
            native = preflight(
                cell, stage, codex, positive, objects, oid, receipts=output / "native"
            )
        controls["native_tools"] = {
            "status": native["controls"]["network"]["status"],
            "evidence": native,
        }
        controls["descendant_budget"] = native["controls"]["budget"]
        if set(controls) != GATES or any(c.get("status") != "passed" for c in controls.values()):
            raise ValueError("runtime qualification has incomplete required controls")
        if harness_hashes() != initial:
            raise ValueError("harness changed during runtime qualification")
        return {
            "status": "passed",
            "gates": controls,
            "runner_hashes": initial,
            "native_package": package_identity(codex),
            "model_calls": 0,
        }

    result = supervise(output, seconds, work)
    write_json(output / "runtime-qualification.json", result)
    return result
