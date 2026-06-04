from __future__ import annotations

from typing import Any


def row_text(row: dict[str, Any]) -> str:
    return " ".join(str(value) for value in row.values() if value is not None)


def table_candidates(rows: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
    lowered = keyword.lower()
    return [row for row in rows if lowered in row_text(row).lower()]


def metadata_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = sorted({key for row in rows for key in row.keys()})
    values_by_key = {
        key: sorted({str(row.get(key)) for row in rows if row.get(key) not in (None, "")})[:30]
        for key in keys
    }
    return {"row_count": len(rows), "keys": keys, "sample_values": values_by_key}

