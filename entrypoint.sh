#!/bin/sh
set -e

# DATABASE_DIR is an environment variable set in the Dockerfile (e.g., /app/data)
# app.py constructs the full path to ben.db using this directory.
DB_FILE_PATH="${DATABASE_DIR}/ben.db"

# Check if the database file already exists in the volume
if [ ! -f "$DB_FILE_PATH" ]; then
  echo "Database not found at $DB_FILE_PATH. Initializing database..."
  # The init_db function in app.py will create the database
  # in the directory specified by DATABASE_DIR (the mounted volume).
  uv run python -c "from app import init_db; init_db()"
  echo "Database initialized."
  
  # Populate the database with surname data if the HTML file exists
  if [ -f "/app/Lintukoto _ Viihde _ Ben.html" ]; then
    echo "Populating database with surname data..."
    uv run python /app/parse_surnames.py
    echo "Database populated with surname data."
  else
    echo "HTML file not found. Database created but not populated with surnames."
  fi
else
  echo "Database found at $DB_FILE_PATH."
fi

# Now, execute the command passed as arguments to this script (the CMD from Dockerfile)
exec "$@"
