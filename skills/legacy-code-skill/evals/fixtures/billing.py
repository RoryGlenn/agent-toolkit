"""Original legacy-change fixture: row order, cent rounding, writes, and audit matter."""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

AUDIT: list[tuple[str, int]] = []


def export_invoice(rows: list[tuple[str, int, str]], destination: Path) -> int:
    lines, total = [], 0
    for sku, quantity, price in rows:
        cents = int((Decimal(price) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        lines.append(f"{sku},{quantity},{cents}\n")
        total += quantity * cents
    destination.write_text("".join(lines), encoding="utf-8")
    AUDIT.append((str(destination), total))
    return total
