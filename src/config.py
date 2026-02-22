"""
Configuration values for the Supply Chain RAG project.

Keeping paths and constants in one place makes it easier to:
- switch between database versions
- change where the SQLite file lives
- reuse the same settings across modules
"""

from pathlib import Path

# Root of the project (this file lives in src/, so go one level up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory where we'll store the actual SQLite file used by the RAG system.
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Path to the SQLite database file that our code will read/write.
SQLITE_DB_PATH = DATA_DIR / "supply_chain.db"

# Path to the directory that contains the SQL scripts for creating/populating the DB.
DATABASE_DIR = PROJECT_ROOT / "Database"

# By default, use the optimized V2.0 scripts as our data source.
V2_DIR = DATABASE_DIR / "V2.0"
V1_DIR = DATABASE_DIR / "V1.0"

# Path to the schema definition for the optimized_supply_chain database.
# This file contains the CREATE TABLE statements for the V2.0 schema.
TABLE_CREATION_SQL = PROJECT_ROOT / "Table_Creation.sql"

