"""RecordBatch: a deliberately small SQLite job service used by development tasks."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import Any

Json = dict[str, Any]


class Store:
    """Manage tenant jobs in one SQLite database.

    Parameters
    ----------
    path
        SQLite file; committed transactions survive process restart.
    principal
        Authenticated tenant identity. It must match each operation's tenant.
    """

    def __init__(self, path: str, principal: str) -> None:
        self.path = path
        self.principal = principal
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY, tenant TEXT NOT NULL,
                    request_id TEXT NOT NULL, payload TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'queued', slot INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(tenant, request_id));
                CREATE TABLE IF NOT EXISTS capacity (
                    tenant TEXT PRIMARY KEY, used INTEGER NOT NULL DEFAULT 0,
                    maximum INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS effects (
                    tenant TEXT NOT NULL, event_id TEXT NOT NULL, delta INTEGER NOT NULL,
                    PRIMARY KEY(tenant, event_id));
                CREATE TABLE IF NOT EXISTS balances (
                    tenant TEXT PRIMARY KEY, value INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS inbox (
                    tenant TEXT NOT NULL, event_id TEXT NOT NULL, acked INTEGER DEFAULT 0,
                    PRIMARY KEY(tenant, event_id));
                CREATE TABLE IF NOT EXISTS deliveries (
                    tenant TEXT NOT NULL, delivery_id TEXT NOT NULL, state TEXT NOT NULL,
                    PRIMARY KEY(tenant, delivery_id));
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
            if "slot" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN slot INTEGER NOT NULL DEFAULT 1")
                connection.execute(
                    "UPDATE jobs SET slot=0 WHERE state IN ('completed', 'cancelled')"
                )
            connection.execute(
                "INSERT OR IGNORE INTO capacity(tenant,used) "
                "SELECT tenant, SUM(slot) FROM jobs GROUP BY tenant"
            )
            connection.execute("PRAGMA user_version=2")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Return an independent connection with a bounded lock wait."""
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def authorize(self, tenant: str) -> None:
        """Reject access outside the authenticated tenant."""
        if self.principal != tenant:
            raise PermissionError("forbidden")

    @staticmethod
    def job(row: sqlite3.Row) -> Json:
        """Return the stable public job representation."""
        return {
            "id": row["id"],
            "tenant": row["tenant"],
            "key": row["request_id"],
            "payload": json.loads(row["payload"]),
            "state": row["state"],
        }

    def submit(self, tenant: str, key: str, payload: Json, fault: str = "") -> Json:
        """Create or recover one request identity without oversubscribing capacity."""
        self.authorize(tenant)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM jobs WHERE tenant=? AND request_id=?", (tenant, key)
            ).fetchone()
            if existing is not None:
                if existing["payload"] != encoded:
                    raise ValueError("conflict")
                return self.job(existing)
            connection.execute("INSERT OR IGNORE INTO capacity(tenant) VALUES (?)", (tenant,))
            reserved = connection.execute(
                "UPDATE capacity SET used=used+1 WHERE tenant=? AND used<maximum", (tenant,)
            ).rowcount
            if not reserved:
                raise ValueError("capacity")
            if fault == "insert":
                raise sqlite3.IntegrityError("injected insertion failure")
            cursor = connection.execute(
                "INSERT INTO jobs(tenant,request_id,payload) VALUES(?,?,?)", (tenant, key, encoded)
            )
            row = connection.execute(
                "SELECT * FROM jobs WHERE id=?", (cursor.lastrowid,)
            ).fetchone()
            assert row is not None
            return self.job(row)

    def submit_many(self, tenant: str, requests: Iterable[Json]) -> list[Json]:
        """Submit any iterable in order, returning one explicit result per request."""
        self.authorize(tenant)
        results: list[Json] = []
        for request in requests:
            try:
                results.append(
                    {"ok": True, "job": self.submit(tenant, request["key"], request["payload"])}
                )
            except (ValueError, sqlite3.Error) as error:
                results.append({"ok": False, "error": error_code(error)})
        return results

    def delete(self, tenant: str, job_id: int) -> None:
        """Delete a job, allowing absence but retaining authorization and storage errors."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT slot FROM jobs WHERE tenant=? AND id=?", (tenant, job_id)
            ).fetchone()
            if row is None:
                return
            connection.execute("DELETE FROM jobs WHERE tenant=? AND id=?", (tenant, job_id))
            if row["slot"]:
                connection.execute("UPDATE capacity SET used=used-1 WHERE tenant=?", (tenant,))

    def status(self, tenant: str, state: str | None = None) -> list[Json]:
        """List this tenant's jobs, optionally filtering by state."""
        self.authorize(tenant)
        if state is not None and state not in {"queued", "running", "completed", "cancelled"}:
            raise ValueError("invalid_state")
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs WHERE tenant=? AND (? IS NULL OR state=?) ORDER BY id",
                (tenant, state, state),
            )
            return [self.job(row) for row in rows]

    def transition(self, tenant: str, job_id: int, action: str, fault: str = "") -> Json:
        """Serialize cancellation, completion, and resumption with capacity ownership."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM jobs WHERE tenant=? AND id=?", (tenant, job_id)
            ).fetchone()
            if row is None:
                raise ValueError("not_found")
            state = row["state"]
            if action == "resume":
                if state == "completed":
                    raise ValueError("completed")
                if state == "cancelled":
                    changed = connection.execute(
                        "UPDATE capacity SET used=used+1 WHERE tenant=? AND used<maximum", (tenant,)
                    ).rowcount
                    if not changed:
                        raise ValueError("capacity")
                    connection.execute(
                        "UPDATE jobs SET state='queued',slot=1 WHERE id=?", (job_id,)
                    )
            elif action in {"cancel", "complete"}:
                if state not in {"completed", "cancelled"}:
                    next_state = "cancelled" if action == "cancel" else "completed"
                    connection.execute(
                        "UPDATE jobs SET state=?,slot=0 WHERE id=?", (next_state, job_id)
                    )
                    if row["slot"]:
                        connection.execute(
                            "UPDATE capacity SET used=used-1 WHERE tenant=?", (tenant,)
                        )
            else:
                raise ValueError("invalid_action")
            if fault == "transition":
                raise sqlite3.IntegrityError("injected transition failure")
            updated = connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            assert updated is not None
            return self.job(updated)

    def effect(self, tenant: str, event_id: str, delta: int, fault: str = "") -> int:
        """Apply one database effect per durable business identity, including replay."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            inserted = connection.execute(
                "INSERT OR IGNORE INTO effects VALUES(?,?,?)", (tenant, event_id, delta)
            ).rowcount
            if inserted:
                connection.execute(
                    "INSERT INTO balances VALUES(?,?) ON CONFLICT(tenant) "
                    "DO UPDATE SET value=value+excluded.value",
                    (tenant, delta),
                )
            connection.execute("INSERT OR IGNORE INTO inbox VALUES(?,?,0)", (tenant, event_id))
            if fault == "before_commit":
                os._exit(75)
        if fault == "after_commit":
            os._exit(75)
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM balances WHERE tenant=?", (tenant,)
            ).fetchone()
            return int(row[0]) if row is not None else 0

    def acknowledge(self, tenant: str, event_id: str) -> None:
        """Mark an inbox receipt acknowledged; this does not expire business identity."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute(
                "UPDATE inbox SET acked=1 WHERE tenant=? AND event_id=?", (tenant, event_id)
            )

    def cleanup(self, tenant: str) -> None:
        """Remove acknowledged inbox records while retaining durable effect identities."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute("DELETE FROM inbox WHERE tenant=? AND acked=1", (tenant,))

    def deliver(self, tenant: str, delivery_id: str, provider: Callable[[], None]) -> str:
        """Attempt a non-idempotent external effect without inventing timeout certainty."""
        self.authorize(tenant)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT state FROM deliveries WHERE tenant=? AND delivery_id=?",
                (tenant, delivery_id),
            ).fetchone()
            if existing is not None and existing["state"] != "rejected":
                return str(existing["state"])
            connection.execute(
                "INSERT INTO deliveries VALUES(?,?,'unknown') ON CONFLICT(tenant,delivery_id) "
                "DO UPDATE SET state='unknown'",
                (tenant, delivery_id),
            )
        # A committed unknown record fences retries if this process exits around the call.
        try:
            provider()
        except TimeoutError:
            state = "unknown"
        except ValueError:
            state = "rejected"  # Provider contract: rejection proves no effect.
        else:
            state = "delivered"
        with self.connect() as connection:
            connection.execute(
                "UPDATE deliveries SET state=? WHERE tenant=? AND delivery_id=?",
                (state, tenant, delivery_id),
            )
        return state


def error_code(error: Exception) -> str:
    """Map only known application and storage failures to stable public errors."""
    if isinstance(error, sqlite3.Error):
        return "storage"
    if isinstance(error, PermissionError):
        return "forbidden"
    return str(error)


def render(jobs: list[Json], adapter: str = "json") -> str:
    """Render a stable job view through the requested output adapter."""
    if adapter == "json":
        return json.dumps(jobs, sort_keys=True)
    if adapter == "csv":
        import csv
        import io

        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["id", "tenant", "key", "state"])
        writer.writerows((job["id"], job["tenant"], job["key"], job["state"]) for job in jobs)
        return stream.getvalue()
    raise ValueError("unknown_adapter")


def request(path: str, data: Json) -> Json:
    """Run one authenticated operation and return an explicit JSON outcome."""
    tenant = data.get("tenant", "demo")
    store = Store(path, str(data.get("principal", tenant)))
    operation = data["op"]
    try:
        if operation == "submit":
            return {
                "ok": True,
                "job": store.submit(tenant, data["key"], data["payload"], data.get("fault", "")),
            }
        if operation == "submit_many":
            return {"ok": True, "results": store.submit_many(tenant, data["requests"])}
        if operation == "status":
            return {"ok": True, "jobs": store.status(tenant, data.get("state"))}
        if operation == "render":
            return {"ok": True, "output": render(store.status(tenant), data.get("adapter", "json"))}
        if operation == "delete":
            store.delete(tenant, int(data["id"]))
        elif operation in {"cancel", "complete", "resume"}:
            return {
                "ok": True,
                "job": store.transition(tenant, int(data["id"]), operation, data.get("fault", "")),
            }
        elif operation == "effect":
            return {
                "ok": True,
                "value": store.effect(
                    tenant, data["event_id"], int(data["delta"]), data.get("fault", "")
                ),
            }
        elif operation == "ack":
            store.acknowledge(tenant, data["event_id"])
        elif operation == "cleanup":
            store.cleanup(tenant)
        elif operation == "init":
            store.authorize(tenant)
        else:
            raise ValueError("unknown_operation")
        return {"ok": True}
    except (PermissionError, ValueError, sqlite3.Error) as error:
        return {"ok": False, "error": error_code(error)}


def main() -> None:
    """Execute the public JSON request CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="state.sqlite")
    parser.add_argument("command", choices=["request"])
    parser.add_argument("json_request")
    arguments = parser.parse_args()
    try:
        data = json.loads(arguments.json_request)
        if not isinstance(data, dict):
            raise ValueError("request must be an object")
        result = request(arguments.db, data)
    except (ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(json.dumps({"ok": False, "error": error_code(error)}))
        raise SystemExit(2) from error
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
