"""SQLite export backend."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel


def _rows(records: Iterable[BaseModel]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        row = record.model_dump(mode="json")
        for key, value in list(row.items()):
            if isinstance(value, (list, dict)):
                row[key] = json.dumps(value)
        rows.append(row)
    return rows


def _write_table(conn: sqlite3.Connection, table: str, records: Iterable[BaseModel]) -> None:
    rows = _rows(records)
    conn.execute(f'DROP TABLE IF EXISTS "{table}"')
    if not rows:
        conn.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
        return
    columns = list(rows[0].keys())
    column_sql = ", ".join(f'"{column}" TEXT' for column in columns)
    conn.execute(f'CREATE TABLE "{table}" ({column_sql})')
    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(f'"{column}"' for column in columns)
    conn.executemany(
        f'INSERT INTO "{table}" ({column_names}) VALUES ({placeholders})',
        [[row.get(column) for column in columns] for row in rows],
    )


def write_sqlite(path: Path, **tables: Iterable[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        for table, records in tables.items():
            _write_table(conn, table, records)
        conn.commit()

