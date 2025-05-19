import os  # Added import
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Define the directory for the database, configurable via environment variable
# Defaults to a 'data' subdirectory in the app's root if not set.
DATABASE_PARENT_DIR = Path(os.getenv("DATABASE_DIR", Path(__file__).parent / "data"))
DATABASE = DATABASE_PARENT_DIR / "ben.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Allows accessing columns by name
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    # Ensure the database directory exists
    DATABASE_PARENT_DIR.mkdir(
        parents=True, exist_ok=True
    )  # Ensure directory is created
    with app.app_context():
        db = get_db()
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()


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
            "UPDATE guesses SET count = ? WHERE surname = ?", (new_count, surname)
        )
    else:
        cursor.execute(
            "INSERT INTO guesses (surname, count) VALUES (?, ?)", (surname, 1)
        )

    db.commit()

    # Redirect to results page, passing the submitted surname for highlighting
    return redirect(url_for("results", highlight=surname))


@app.route("/results")
def results():
    highlight_surname = request.args.get("highlight")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT surname, count FROM guesses ORDER BY surname ASC")
    all_guesses = cursor.fetchall()

    return render_template(
        "results.html", guesses=all_guesses, highlight_surname=highlight_surname
    )


if __name__ == "__main__":
    # Create schema.sql before running for the first time
    # For simplicity, we'll create it here if it doesn't exist,
    # or you can create it manually.
    # init_db() # Call this manually or ensure schema.sql exists and is run
    app.run(debug=True)
