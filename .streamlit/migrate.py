"""SQLite migrations for the Rizzk stack."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

DEFAULT_DB = Path("./data/rizzk.db")


def migrate(db: Union[str, Path] = DEFAULT_DB) -> None:
    """Ensure baseline tables exist and enable WAL mode."""

    path = Path(db)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS meta(\n                key TEXT PRIMARY KEY,\n                val TEXT\n            )"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS trades(\n                id INTEGER PRIMARY KEY,\n                date TEXT,\n                symbol TEXT,\n                pnl REAL,\n                rr REAL,\n                win INT\n            )"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS kpi_daily(\n                date TEXT PRIMARY KEY,\n                pnl REAL,\n                win_rate REAL,\n                rr_avg REAL,\n                n INT\n            )"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS alerts(\n                alert_id TEXT PRIMARY KEY,\n                symbol TEXT,\n                rule TEXT,\n                cooldown_min INT,\n                last_fired_ts INT\n            )"
        )
        con.commit()


__all__ = ["migrate"]
