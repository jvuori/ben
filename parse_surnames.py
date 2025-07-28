#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "beautifulsoup4",
#     "lxml",
# ]
# ///
"""Script to parse Ben Zyskowicz surname variations from HTML file and populate database."""

import os
import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup


def get_database_path():
    """Get the database path, matching the same logic as app.py and setup_db.py."""
    database_dir = Path(os.getenv("DATABASE_DIR", Path(__file__).parent / "data"))
    return database_dir / "ben.db"


def parse_html_table(html_file_path):
    """Parse the HTML file and extract surname variations with their counts."""
    with open(html_file_path, encoding="windows-1252") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # Find all table rows
    rows = soup.find_all("tr", class_="vaalein")

    surnames_data = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            # Get the surname(s) from the second cell
            surname_cell = cells[1]
            surname_text = surname_cell.get_text(strip=True)

            # Get the count from the third cell
            count_cell = cells[2]
            count_text = count_cell.get_text(strip=True)

            # Skip the first row with "Zyskowicz (oikea vastaus)"
            if "oikea vastaus" in surname_text:
                continue

            # Parse count (remove spaces and convert to int)
            try:
                count = int(count_text.replace(" ", "").replace("\u00a0", ""))
            except ValueError:
                print(f"Could not parse count: {count_text}")
                continue

            # Handle multiple surnames separated by commas
            surnames = [name.strip() for name in surname_text.split(",")]

            for surname in surnames:
                # Clean up the surname (remove extra whitespace)
                surname = surname.strip()
                if surname:
                    surnames_data.append((surname, count))

    return surnames_data


def create_database_connection(db_path):
    """Create a connection to the SQLite database."""
    return sqlite3.connect(db_path)


def populate_database(surnames_data, db_path):
    """Populate the database with surname variations."""
    conn = create_database_connection(db_path)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM guesses")

    # Insert new data
    inserted_count = 0
    for surname, count in surnames_data:
        try:
            cursor.execute(
                "INSERT INTO guesses (surname, count) VALUES (?, ?)",
                (surname, count),
            )
            inserted_count += 1
        except sqlite3.IntegrityError:
            # Handle duplicate surnames (should not happen with our data)
            print(f"Duplicate surname found: {surname}")

    conn.commit()
    conn.close()

    print(
        f"Successfully inserted {inserted_count} surname variations into the database.",
    )
    return inserted_count


def main():
    """Parse HTML and populate database."""
    # Paths
    html_file = Path("Lintukoto _ Viihde _ Ben.html")
    db_file = get_database_path()

    if not html_file.exists():
        print(f"HTML file not found: {html_file}")
        return

    if not db_file.exists():
        print(f"Database file not found: {db_file}")
        print("Please run setup_db.py first to create the database.")
        return

    print("Parsing HTML file...")
    surnames_data = parse_html_table(html_file)

    print(f"Found {len(surnames_data)} surname entries.")

    # Show some examples
    print("\nFirst 10 entries:")
    for i, (surname, count) in enumerate(surnames_data[:10]):
        print(f"  {i + 1}. {surname} - {count}")

    print("\nPopulating database...")
    populate_database(surnames_data, db_file)

    # Verify the data was inserted
    conn = create_database_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM guesses")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT surname, count FROM guesses ORDER BY count DESC LIMIT 5")
    top_5 = cursor.fetchall()

    conn.close()

    print(f"\nDatabase now contains {total_count} surname variations.")
    print("\nTop 5 most common incorrect spellings:")
    for i, (surname, count) in enumerate(top_5, 1):
        print(f"  {i}. {surname} - {count}")


if __name__ == "__main__":
    main()
