#!/bin/sh
set -e

# DATABASE_DIR is an environment variable set in the Dockerfile (e.g., /database_volume)
# app.py constructs the full path to ben.db using this directory.
DB_FILE_PATH="${DATABASE_DIR}/ben.db"

# Check if the database file already exists in the volume
if [ ! -f "$DB_FILE_PATH" ]; then
  echo "Database not found at $DB_FILE_PATH. Initializing database..."
  # The init_db function in app.py will create the database
  # in the directory specified by DATABASE_DIR (the mounted volume).
  python -c "from app import init_db; init_db()"
  echo "Database initialized."
else
  echo "Database found at $DB_FILE_PATH."
fi

# Now, execute the command passed as arguments to this script (the CMD from Dockerfile)
exec "$@"
