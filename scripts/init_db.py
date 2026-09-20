"""Initialize the local SQLite database from the schema file."""

from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "app" / "db" / "schema.sql"
DATABASE_PATH = PROJECT_ROOT / "lead_automation.db"


def initialize_database() -> Path:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(schema)
        connection.commit()

    return DATABASE_PATH


if __name__ == "__main__":
    path = initialize_database()
    print(f"Initialized database: {path}")
