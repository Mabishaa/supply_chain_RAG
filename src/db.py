"""
Database utilities for the Supply Chain RAG project.

This module is responsible for:
- creating/loading the SQLite database file from the existing SQL scripts
- providing a simple, reusable connection helper
- exposing basic query helpers that other modules (e.g. RAG) can import

Keeping DB logic in one place makes it easier to:
- switch DB versions
- debug SQL issues
- later plug in SQL-aware agents without touching RAG code
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List, Tuple

try:
    # When used as part of the `src` package (e.g. `python -m src.simple_qa`)
    from .config import SQLITE_DB_PATH, V2_DIR, TABLE_CREATION_SQL
except ImportError:
    # When modules are imported directly from the `src` folder (e.g. via Streamlit)
    from config import SQLITE_DB_PATH, V2_DIR, TABLE_CREATION_SQL


def get_connection() -> sqlite3.Connection:
    """
    Return a SQLite connection to the main project database.

    WHY: Having a single function for this avoids duplicating the path/flags
    everywhere and lets us centralize connection options (e.g. row factory).
    """
    conn = sqlite3.connect(SQLITE_DB_PATH)
    # Return rows as dict-like objects (accessible by column name).
    conn.row_factory = sqlite3.Row
    return conn


def _read_sql_file(path) -> str:
    """
    Read a .sql file and return its contents as a string.

    WHY: We keep SQL in separate files for clarity and version control.
    This helper isolates the I/O so the loader logic stays clean.
    """
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _normalize_sql_for_sqlite(sql: str) -> str:
    """
    Very small adapter to make MySQL-oriented SQL work in SQLite:

    - Removes `USE optimized_supply_chain;` statements (not supported in SQLite)
    - Strips the `optimized_supply_chain.` schema prefix from table names

    This is intentionally minimal; for this project we only need these tweaks.
    """
    # Remove any 'USE optimized_supply_chain;' statements (case-insensitive).
    sql = sql.replace("use optimized_supply_chain;", "")
    sql = sql.replace("USE optimized_supply_chain;", "")

    # Drop the schema qualifier from table references.
    sql = sql.replace("optimized_supply_chain.", "")

    # The inventory_stocks table has a composite PRIMARY KEY
    # (inventory_id, product_id). The source data file may contain
    # duplicate rows for the same key. In SQLite, that causes a
    # UNIQUE constraint error, whereas MySQL often uses INSERT IGNORE.
    #
    # To keep the DB load simple and robust for this academic project,
    # we convert plain INSERTs on this table into INSERT OR IGNORE.
    # Handle both lowercase and uppercase INSERT forms.
    sql = sql.replace(
        "insert into inventory_stocks",
        "INSERT OR IGNORE INTO inventory_stocks",
    )
    sql = sql.replace(
        "INSERT INTO inventory_stocks",
        "INSERT OR IGNORE INTO inventory_stocks",
    )

    return sql


def initialize_database(force_recreate: bool = False) -> None:
    """
    Create (or recreate) the SQLite database from the schema + V2.0 SQL scripts.

    - If `force_recreate` is True, we delete and rebuild the DB from scratch.
    - If the DB already exists and `force_recreate` is False, we do nothing.

    WHY: This makes your project reproducible. Anyone can run this function
    and get the same local SQLite DB from the checked-in SQL scripts.
    """
    db_path = SQLITE_DB_PATH

    if db_path.exists():
        if not force_recreate:
            # Database is already there; nothing to do.
            return
        db_path.unlink()

    # Create an empty database file by opening a connection.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        # 1) Create the schema (tables, relationships) from Table_Creation.sql
        if not TABLE_CREATION_SQL.exists():
            raise FileNotFoundError(f"Schema file not found: {TABLE_CREATION_SQL}")

        schema_sql = _read_sql_file(TABLE_CREATION_SQL)
        schema_sql = _normalize_sql_for_sqlite(schema_sql)
        cursor.executescript(schema_sql)

        # 2) Populate the tables with data from the V2.0 insert scripts.
        # NOTE: You can adjust this list if you change your data files.
        sql_files_in_order = [
            "optimized_supply_chain.suppliers.sql",
            "optimized_supply_chain.products.sql",
            "optimized_supply_chain.inventory_stocks.sql",
            "optimized_supply_chain.orders.sql",
            "optimized_supply_chain.customer_orders.sql",
            "optimized_supply_chain.purchase_orders.sql",
            "optimized_supply_chain.supplies.sql",
            "supply_chain_group22.customers.sql",
            "supply_chain_group22.inventory.sql",
            "supply_chain_group22. customer_contacts.sql",
        ]

        for filename in sql_files_in_order:
            sql_path = V2_DIR / filename
            if not sql_path.exists():
                raise FileNotFoundError(f"Expected SQL file not found: {sql_path}")

            sql_script = _read_sql_file(sql_path)
            sql_script = _normalize_sql_for_sqlite(sql_script)
            cursor.executescript(sql_script)

        conn.commit()
    finally:
        conn.close()


def run_query(
    query: str,
    params: Tuple[Any, ...] | Iterable[Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Run a SELECT query and return the results as a list of dicts.

    WHY: This provides a very simple, typed interface for higher-level
    code (like RAG components) that shouldn't worry about sqlite3 details.
    """
    if params is None:
        params = ()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_schema_description() -> str:
    """
    Introspect the database and return a human-readable schema description
    for use in NL2SQL prompts.

    WHY: The LLM needs to know table names, column names, and types to
    generate correct SQL from natural language questions.
    """
    lines: List[str] = []
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            columns = cur.fetchall()
            col_parts = [f"{c[1]} ({c[2]})" for c in columns]
            lines.append(f"- {table}({', '.join(col_parts)})")

    return "Database schema (SQLite):\n" + "\n".join(lines)


def get_sample_rows(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch a small sample of rows from a key table (e.g. products) for testing.

    WHY: This is used in Phase 1 to quickly verify that:
    - the DB was initialized correctly
    - we can successfully read data
    """
    # Adjust this table name/columns to match your actual optimized schema.
    # We'll start with the products table from the V2 scripts, since it is
    # definitely populated with data.
    query = """
        SELECT *
        FROM products
        LIMIT ?
    """
    return run_query(query, (limit,))


if __name__ == "__main__":
    # Simple smoke test for manual runs:
    #   python -m src.db
    initialize_database(force_recreate=False)
    rows = get_sample_rows(limit=3)
    print(f"Fetched {len(rows)} rows from 'customers':")
    for r in rows:
        print(r)

