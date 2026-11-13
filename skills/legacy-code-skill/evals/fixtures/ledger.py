"""Original fixture with deliberately unavailable live construction."""


def connect_database(dsn: str) -> object:
    raise RuntimeError(f"Live database unavailable for {dsn}")


class Ledger:
    def __init__(self, dsn: str) -> None:
        self.connection = connect_database(dsn)

    def total(self) -> int:
        return sum(self.connection.fetch_amounts())  # type: ignore[attr-defined]
