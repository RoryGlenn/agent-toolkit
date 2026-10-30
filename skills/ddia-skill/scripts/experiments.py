#!/usr/bin/env python3
"""Run bounded DDIA counterexamples with deliberately broken and sufficient controls."""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import threading
from contextlib import closing
from pathlib import Path
from typing import Any


def admission(atomic: bool) -> dict[str, Any]:
    """Exercise two admissions against one unit using actual SQLite transactions."""
    with tempfile.TemporaryDirectory(prefix="ddia-admission-") as temporary:
        database = Path(temporary) / "inventory.sqlite"
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.executescript(
                "CREATE TABLE stock (remaining INTEGER NOT NULL); INSERT INTO stock VALUES (1);"
                "CREATE TABLE admissions (identity TEXT PRIMARY KEY);"
            )
        barrier = threading.Barrier(2, timeout=10)
        errors: list[str] = []

        def worker(identity: str) -> None:
            connection = sqlite3.connect(database, timeout=10)
            try:
                remaining = int(connection.execute("SELECT remaining FROM stock").fetchone()[0])
                barrier.wait()
                with connection:
                    if atomic:
                        changed = connection.execute(
                            "UPDATE stock SET remaining=remaining-1 WHERE remaining>0"
                        ).rowcount
                    else:
                        changed = remaining > 0
                        if changed:
                            connection.execute("UPDATE stock SET remaining=?", (remaining - 1,))
                    if changed:
                        connection.execute("INSERT INTO admissions VALUES (?)", (identity,))
            except (sqlite3.Error, threading.BrokenBarrierError) as error:
                errors.append(str(error))
            finally:
                connection.close()

        workers = [threading.Thread(target=worker, args=(str(i),), daemon=True) for i in range(2)]
        for thread in workers:
            thread.start()
        for thread in workers:
            thread.join(timeout=15)
        if errors or any(thread.is_alive() for thread in workers):
            raise RuntimeError(f"Admission experiment could not complete: {errors}")
        with closing(sqlite3.connect(database)) as connection:
            count = int(connection.execute("SELECT count(*) FROM admissions").fetchone()[0])
            remaining = int(connection.execute("SELECT remaining FROM stock").fetchone()[0])
        return {"admitted": count, "remaining": remaining, "invariant": count <= 1}


def replay(retain_identity: bool) -> dict[str, Any]:
    """Exercise local effect/identity commit, failed acknowledgement and later replay."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            "CREATE TABLE seen (identity TEXT PRIMARY KEY);"
            "CREATE TABLE effects (count INTEGER); INSERT INTO effects VALUES (0);"
        )

        def deliver(crash_before_commit: bool = False) -> None:
            with connection:
                inserted = connection.execute(
                    "INSERT OR IGNORE INTO seen VALUES ('event-1')"
                ).rowcount
                if inserted:
                    connection.execute("UPDATE effects SET count=count+1")
                if crash_before_commit:
                    raise RuntimeError("simulated failure before transaction commit")

        try:
            deliver(True)
        except RuntimeError:
            pass
        deliver()  # commit succeeds, acknowledgement is lost
        deliver()  # redelivery before acknowledgement
        if not retain_identity:
            with connection:
                connection.execute("DELETE FROM seen")  # cleanup following acknowledgement
        deliver()  # operational replay, same business state
        effects = int(connection.execute("SELECT count FROM effects").fetchone()[0])
        return {"effects": effects, "invariant": effects == 1}
    finally:
        connection.close()


def fencing(enforced: bool) -> dict[str, Any]:
    """Model resource validation after an old leaseholder resumes; no real lock service."""
    largest_token = 0
    value = "initial"
    accepted = []
    for token, writer in ((2, "new-owner"), (1, "paused-old-owner")):
        if enforced and token < largest_token:
            continue
        largest_token = max(largest_token, token)
        value = writer
        accepted.append(writer)
    return {"accepted": accepted, "value": value, "invariant": value == "new-owner"}


def temporal(versioned: bool) -> dict[str, Any]:
    """Model replay enrichment using historical versus latest reference values."""
    rates = [(0, 0.10), (20, 0.20)]
    event_time, amount = 10, 100
    first = amount * rates[0][1]
    rate = max((item for item in rates if item[0] <= event_time), key=lambda item: item[0])[1]
    replayed = amount * (rate if versioned else rates[-1][1])
    return {"original": first, "replayed": replayed, "invariant": replayed == first}


def identity(binding: bool) -> dict[str, Any]:
    """Model stable identity reused with a different business payload."""
    stored_payload, requested_payload = "transfer:alice:10", "transfer:bob:90"
    response = "conflict" if binding and stored_payload != requested_payload else "success"
    return {"response": response, "invariant": response == "conflict"}


def compatibility(preserve_unknown: bool) -> dict[str, Any]:
    """Round-trip JSON through an old client and expose unknown-field loss."""
    original = json.loads('{"name":"Ada","privacy":"private"}')
    old_view = dict(original) if preserve_unknown else {"name": original["name"]}
    old_view["name"] = "Ada L."
    restored = json.loads(json.dumps(old_view))
    return {"record": restored, "invariant": restored.get("privacy") == "private"}


def publication(version_pointer: bool) -> dict[str, Any]:
    """Model interruption during a two-partition publication, not filesystem crash durability."""
    old = {"part-a": 1, "part-b": 1}
    staged = {"part-a": 2, "part-b": 2}
    observed = dict(old)
    if not version_pointer:
        observed["part-a"] = staged["part-a"]
    # Failure before publication: an authoritative version pointer still selects old.
    return {"visible": observed, "invariant": len(set(observed.values())) == 1}


def deletion(respect_tombstone: bool) -> dict[str, Any]:
    """Model projection rebuild with a retained deletion policy."""
    source = {"person-1": {"name": "Ada"}}
    deleted = {"person-1"}
    rebuilt = {
        key: value for key, value in source.items() if not respect_tombstone or key not in deleted
    }
    return {"rebuilt": rebuilt, "invariant": "person-1" not in rebuilt}


EXPERIMENTS = {
    "atomic-admission": (admission, "SQLite transactions and a forced two-reader schedule"),
    "message-replay": (replay, "SQLite local effects with simulated acknowledgement/replay"),
    "lease-fencing": (fencing, "Deterministic resource model; no network or real lease service"),
    "temporal-join": (temporal, "Deterministic historical-enrichment model; no stream engine"),
    "payload-identity": (identity, "Deterministic identity/payload model; no provider API"),
    "schema-roundtrip": (compatibility, "Actual JSON round-trip; no protobuf/Avro toolchain"),
    "complete-publication": (publication, "Deterministic publication model; no crash durability"),
    "deletion-rebuild": (deletion, "Deterministic derived-state lifecycle model; no legal claim"),
}


def run(name: str) -> dict[str, Any]:
    """Run both variants and require the oracle to reject broken and accept sufficient."""
    if name not in EXPERIMENTS:
        raise ValueError(f"Unknown experiment: {name}")
    experiment, scope = EXPERIMENTS[name]
    broken, sufficient = experiment(False), experiment(True)
    detected = not broken["invariant"] and sufficient["invariant"]
    if not detected:
        raise RuntimeError(f"Experiment controls failed: {name}")
    return {
        "experiment": name,
        "scope": scope,
        "broken": broken,
        "sufficient": sufficient,
        "controls_passed": detected,
        "limits": "Bounded counterexample only; no caller-project or agent effectiveness claim.",
    }


def main() -> int:
    """Print reproducible control results for one or all bounded experiments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=["all", *EXPERIMENTS])
    args = parser.parse_args()
    results = [run(name) for name in EXPERIMENTS] if args.name == "all" else [run(args.name)]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
