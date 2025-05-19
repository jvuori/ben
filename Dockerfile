# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0

# Declare a volume for the database file
VOLUME /app

# Initialize the database if it doesn't exist
# This assumes you have a way to run init_db() or that the db is pre-populated
# For a more robust solution, consider using a database migration tool or entrypoint script
RUN if [ ! -f ben.db ]; then \
    echo "Initializing database..." && \
    python -c "from app import init_db; init_db()"; \
    fi

# Run app.py when the container launches
CMD ["flask", "run"]
