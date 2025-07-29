#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "beautifulsoup4",
#     "lxml",
# ]
# ///
"""Parse Ben Zyskowicz surname variations from HTML file and populate database.

This script:
1. Parses the Lintukoto HTML data
2. Applies the same validation rules as the web application
3. Handles duplicates by adding counts to existing entries
4. Provides detailed statistics about the import process
"""

import re
import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup

# Constants for validation
MIN_SURNAME_LENGTH = 6
MAX_SURNAME_LENGTH = 15
MIN_TABLE_COLUMNS = 3
VALID_STARTING_LETTERS = ("z", "s", "t", "c")


def is_valid_surname(surname: str) -> bool:
    """Validate a surname using the same rules as the web application.

    - Must start with 'z', 's', 't', or 'c'
    - Length 6-15 characters
    - Only letters (including Nordic letters)
    """
    if (
        not surname
        or len(surname) < MIN_SURNAME_LENGTH
        or len(surname) > MAX_SURNAME_LENGTH
    ):
        return False

    # Convert to lowercase for checking
    surname_lower = surname.lower()

    # Must start with z, s, t, or c
    if not surname_lower.startswith(VALID_STARTING_LETTERS):
        return False

    # Check if only letters (including Nordic letters and accented y)
    return bool(re.match(r"^[a-zA-ZäöåÄÖÅüÜýÝÿŸ]+$", surname))


def clean_surname(surname: str) -> str:
    """Clean a surname by removing HTML tags and normalizing whitespace."""
    # Remove HTML tags if any
    surname = re.sub(r"<[^>]+>", "", surname)

    # Normalize whitespace
    surname = re.sub(r"\s+", " ", surname)

    # Strip leading/trailing whitespace
    return surname.strip()


def get_database_path() -> Path:
    """Get the path to the database file."""
    return Path("ben.db")


def parse_html_table(
    html_file_path: str,
) -> tuple[list[tuple[str, int]], dict[str, int]]:
    """Parse HTML file and extract surname variations with their counts.

    Returns a tuple of (surnames_data, validation_stats) where surnames_data
    is a list of (surname, count) tuples for valid surnames only.
    """
    with Path(html_file_path).open(encoding="windows-1252") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # Find all table rows
    rows = soup.find_all("tr", class_="vaalein")

    surnames_data = []
    validation_stats = {
        "total_entries": 0,
        "total_submissions": 0,
        "valid_entries": 0,
        "valid_submissions": 0,
        "rejected_too_short": 0,
        "rejected_wrong_start": 0,
        "rejected_invalid_chars": 0,
        "rejected_too_long": 0,
    }

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < MIN_TABLE_COLUMNS:
            continue

        # Get the surname(s) from the second cell
        surname_cell = cells[1]
        surname_text = surname_cell.get_text(strip=True)

        # Get the count from the third cell
        count_cell = cells[2]
        count_text = count_cell.get_text(strip=True)

        # Handle the correct answer row specially
        if "oikea vastaus" in surname_text:
            # Extract "Zyskowicz" from "Zyskowicz (oikea vastaus)"
            correct_answer = surname_text.replace("(oikea vastaus)", "").strip()
            if correct_answer:
                # Parse count for the correct answer too
                try:
                    count = int(count_text.replace(" ", "").replace("\u00a0", ""))
                except ValueError:
                    print(f"Could not parse count for correct answer: {count_text}")
                    continue

                validation_stats["total_entries"] += 1
                validation_stats["total_submissions"] += count

                if is_valid_surname(correct_answer):
                    surnames_data.append((correct_answer.lower(), count))
                    validation_stats["valid_entries"] += 1
                    validation_stats["valid_submissions"] += count
                else:
                    # Even if the correct answer doesn't pass validation, we should note it
                    print(
                        f"Warning: Correct answer '{correct_answer}' doesn't pass validation!",
                    )
            continue

        # Parse count (remove spaces and convert to int)
        try:
            count = int(count_text.replace(" ", "").replace("\u00a0", ""))
        except ValueError:
            print(f"Could not parse count: {count_text}")
            continue

        # Handle multiple surnames separated by commas
        surnames = [name.strip() for name in surname_text.split(",")]

        for surname_raw in surnames:
            # Clean up the surname
            surname = clean_surname(surname_raw)
            if not surname:
                continue

            validation_stats["total_entries"] += 1
            validation_stats["total_submissions"] += count

            # Apply validation
            if is_valid_surname(surname):
                surnames_data.append((surname.lower(), count))
                validation_stats["valid_entries"] += 1
                validation_stats["valid_submissions"] += count
            elif len(surname) < MIN_SURNAME_LENGTH:
                print(f"REJECTED (short): '{surname}' len={len(surname)} cnt={count}")
                validation_stats["rejected_too_short"] += 1
            elif len(surname) > MAX_SURNAME_LENGTH:
                print(f"REJECTED (long): '{surname}' len={len(surname)} cnt={count}")
                validation_stats["rejected_too_long"] += 1
            elif not surname.lower().startswith(VALID_STARTING_LETTERS):
                start_char = surname[0] if surname else "N/A"
                print(f"REJECTED (start): '{surname}' '{start_char}' cnt={count}")
                validation_stats["rejected_wrong_start"] += 1
            else:
                print(f"REJECTED (chars): '{surname}' cnt={count}")
                validation_stats["rejected_invalid_chars"] += 1

    return surnames_data, validation_stats


def create_database_connection(db_path: str) -> sqlite3.Connection:
    """Create and return a database connection."""
    return sqlite3.connect(db_path)


def populate_database(
    surnames_data: list[tuple[str, int]],
    db_path: str,
) -> None:
    """Populate database with surname data, handling duplicates by adding counts.

    Args:
        surnames_data: List of (surname, count) tuples
        db_path: Path to the SQLite database file

    """
    conn = create_database_connection(db_path)
    cursor = conn.cursor()

    # First clear existing data
    cursor.execute("DELETE FROM guesses")

    # Aggregate duplicate surnames
    surname_totals: dict[str, int] = {}
    for surname, count in surnames_data:
        if surname in surname_totals:
            surname_totals[surname] += count
        else:
            surname_totals[surname] = count

    # Insert aggregated data
    for surname, total_count in surname_totals.items():
        cursor.execute(
            "INSERT INTO guesses (surname, count) VALUES (?, ?)",
            (surname, total_count),
        )

    conn.commit()
    conn.close()

    print(f"Inserted {len(surname_totals)} unique surnames with total counts.")


def main() -> None:
    """Parse HTML and populate database."""
    html_file_path = "Lintukoto _ Viihde _ Ben.html"
    db_path = "ben.db"

    print("Parsing HTML file...")
    surnames_data, stats = parse_html_table(html_file_path)

    # Print validation statistics
    print("\nValidation Statistics:")
    print(f"Total entries processed: {stats['total_entries']}")
    print(f"Total submissions: {stats['total_submissions']:,}")

    valid_entry_pct = stats["valid_entries"] / stats["total_entries"] * 100
    print(f"Valid entries: {stats['valid_entries']} ({valid_entry_pct:.1f}%)")

    valid_sub_pct = stats["valid_submissions"] / stats["total_submissions"] * 100
    print(f"Valid submissions: {stats['valid_submissions']:,} ({valid_sub_pct:.1f}%)")

    print(f"Rejected - too short: {stats['rejected_too_short']}")
    print(f"Rejected - too long: {stats['rejected_too_long']}")
    print(f"Rejected - wrong start: {stats['rejected_wrong_start']}")
    print(f"Rejected - invalid chars: {stats['rejected_invalid_chars']}")

    print("\nPopulating database...")
    populate_database(surnames_data, db_path)
    print("Database population complete!")


if __name__ == "__main__":
    main()
