import os  # Added import
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


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
    # Get the first word, strip whitespace, and convert to Pascal case
    surname = request.form["surname"].strip().split()[0]
    surname = surname.capitalize() if surname else ""
    if not surname:
        # Or handle error appropriately
        return redirect(url_for("index"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT count FROM guesses WHERE surname = ?", (surname,))
    row = cursor.fetchone()

    if row:
        new_count = row["count"] + 1
        cursor.execute(
            "UPDATE guesses SET count = ? WHERE surname = ?",
            (new_count, surname),
        )
    else:
        cursor.execute(
            "INSERT INTO guesses (surname, count) VALUES (?, ?)",
            (surname, 1),
        )

    db.commit()

    # Redirect to results page, passing the submitted surname for highlighting
    return redirect(url_for("results", highlight=surname))


@app.route("/results")
def results():
    highlight_surname = request.args.get("highlight")
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT surname, count FROM guesses ORDER BY count DESC, surname ASC",
    )
    all_guesses = cursor.fetchall()

    return render_template(
        "results.html",
        guesses=all_guesses,
        highlight_surname=highlight_surname,
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
