"""Test configuration and fixtures for the Ben project."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from app import app


@pytest.fixture
def client() -> Generator[FlaskClient]:
    """Create a test client for the Flask application."""
    # Create a temporary database file for testing
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app.config["TESTING"] = True

    # Override the database path for testing
    os.environ["DATABASE_DIR"] = str(Path(db_path).parent)

    with app.test_client() as client:
        with app.app_context():
            # Initialize test database with schema
            from setup_db import init_db

            init_db()

            # Add some test data
            from app import get_db

            db = get_db()
            cursor = db.cursor()

            # Create test data in guesses table
            cursor.execute(
                "INSERT OR IGNORE INTO guesses (surname, count) VALUES (?, ?)",
                ("TestSurname", 1),
            )
            cursor.execute(
                "INSERT OR IGNORE INTO guesses (surname, count) VALUES (?, ?)",
                ("AnotherTest", 2),
            )
            db.commit()

        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def app_context() -> Generator[None]:
    """Create an application context for testing."""
    with app.app_context():
        yield
