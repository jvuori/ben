#!/usr/bin/env python3
"""Database setup script for the Ben surname guessing game.
Creates the database schema without requiring the Flask application.
"""

import os
import sqlite3
from pathlib import Path


def init_db():
    """Initialize the database with the schema."""
    # Get database directory from environment or use default
    database_dir = Path(os.getenv("DATABASE_DIR", Path(__file__).parent / "data"))
    database_path = database_dir / "ben.db"

    # Ensure the database directory exists
    database_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database and create schema
    conn = sqlite3.connect(database_path)

    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

    print(f"Database initialized at {database_path}")


if __name__ == "__main__":
    init_db()
