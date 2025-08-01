import logging
import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)  # type: ignore[assignment]


# Setup audit logging
def setup_audit_logger() -> logging.Logger:
    """Set up audit logger for user guess submissions."""
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = Path(os.getenv("LOGS_DIR", Path(__file__).parent / "logs"))
    logs_dir.mkdir(exist_ok=True)

    # Create file handler for audit log
    audit_log_path = logs_dir / "audit.log"
    handler = logging.FileHandler(audit_log_path)
    handler.setLevel(logging.INFO)

    # Create formatter for audit logs
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)

    # Add handler to logger if not already added
    if not audit_logger.handlers:
        audit_logger.addHandler(handler)

    return audit_logger


# Initialize audit logger
audit_logger = setup_audit_logger()


def log_user_guess(surname: str, client_ip: str) -> None:
    """Log user guess submission for audit purposes."""
    audit_logger.info("%s - %s", client_ip, surname)


# Constants for validation
MIN_SURNAME_LENGTH = 4  # Minimum for game requirements
MAX_SURNAME_LENGTH = 50


# Length constraints based on data analysis
MIN_SURNAME_LENGTH = 6
MAX_SURNAME_LENGTH = 15


def is_valid_surname(surname: str) -> bool:
    """Validate a surname based on real Lintukoto data analysis.

    - Must start with 'z', 's', 't', or 'c' (covers ~99.6% of valid submissions)
    - Length 6-15 characters (filters out obvious test words)
    - Only letters (including Nordic letters)

    This approach is simple, effective, and based on actual user submission patterns.
    """
    if (
        not surname
        or len(surname) < MIN_SURNAME_LENGTH
        or len(surname) > MAX_SURNAME_LENGTH
    ):
        return False

    # Convert to lowercase for checking
    surname_lower = surname.lower()

    # Must start with z, s, t, or c (covers 99.6% of real submissions)
    if not surname_lower.startswith(("z", "s", "t", "c")):
        return False

    # Check if only letters (including Nordic letters and accented y)
    return bool(re.match(r"^[a-zA-ZäöåÄÖÅüÜýÝÿŸ]+$", surname))


# Define the directory for the database, configurable via environment variable
# Defaults to a 'data' subdirectory in the app's root if not set.
def get_database_path():
    """Get the database path, allowing for runtime environment variable changes."""
    database_dir = Path(os.getenv("DATABASE_DIR", Path(__file__).parent / "data"))
    return database_dir / "ben.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        database_path = get_database_path()
        db = g._database = sqlite3.connect(database_path)
        db.row_factory = sqlite3.Row  # Allows accessing columns by name
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit_guess():
    # Get the surname from form data
    raw_surname = request.form.get("surname", "").strip()

    # Extract first word only and strip whitespace
    surname = raw_surname.split()[0] if raw_surname else ""

    # Server-side validation: check if surname contains only letters
    if not is_valid_surname(surname):
        # Redirect back to index if validation fails
        return redirect(url_for("index"))

    # Normalize to lowercase for database operations (consistent with parser)
    surname_normalized = surname.lower()

    # Get client IP for audit logging
    client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    if client_ip and "," in client_ip:
        # If multiple IPs in X-Forwarded-For, take the first one (original client)
        client_ip = client_ip.split(",")[0].strip()

    # Log the guess for audit purposes
    log_user_guess(surname_normalized, client_ip or "unknown")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT count FROM guesses WHERE surname = ?", (surname_normalized,))
    row = cursor.fetchone()

    if row:
        new_count = row["count"] + 1
        cursor.execute(
            "UPDATE guesses SET count = ? WHERE surname = ?",
            (new_count, surname_normalized),
        )
    else:
        cursor.execute(
            "INSERT INTO guesses (surname, count) VALUES (?, ?)",
            (surname_normalized, 1),
        )

    db.commit()

    # Redirect to results page, passing the normalized surname for highlighting
    return redirect(url_for("results", highlight=surname_normalized))


@app.route("/results")
def results():
    highlight_surname = request.args.get("highlight")
    db = get_db()
    cursor = db.cursor()

    # Get all guesses ordered by count
    cursor.execute(
        "SELECT surname, count FROM guesses ORDER BY count DESC, surname ASC",
    )
    all_guesses = cursor.fetchall()

    # Count total number of different variations
    cursor.execute("SELECT COUNT(*) as total_variations FROM guesses")
    total_variations = cursor.fetchone()["total_variations"]

    # Calculate total count for percentage calculations
    cursor.execute("SELECT SUM(count) as total_count FROM guesses")
    total_count = cursor.fetchone()["total_count"]

    # Add percentage to each guess
    guesses_with_percentages = []
    for guess in all_guesses:
        percentage = (guess["count"] / total_count * 100) if total_count > 0 else 0
        guesses_with_percentages.append(
            {
                "surname": guess["surname"],
                "count": guess["count"],
                "percentage": round(percentage, 2),
            },
        )

    return render_template(
        "results.html",
        guesses=guesses_with_percentages,
        highlight_surname=highlight_surname,
        total_variations=total_variations,
    )


@app.route("/health")
def health():
    """Health check endpoint for container orchestration."""
    try:
        # Test database connectivity
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM guesses LIMIT 1")
        cursor.fetchone()
    except sqlite3.Error as e:
        return {"status": "unhealthy", "error": str(e)}, 500
    else:
        return {"status": "healthy", "database": "connected"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # Bind to all interfaces when running in container
    app.run(host="0.0.0.0", port=port, debug=False)  # noqa: S104
