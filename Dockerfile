# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install dependencies using uv
RUN uv sync

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV DATABASE_DIR /app/data
ENV LOGS_DIR /app/logs

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Ensure the logs directory is writable
RUN chmod 755 /app/logs

# Declare volumes for external mounting
VOLUME ["/app/data", "/app/logs"]

# The CMD runs the Flask application directly
CMD ["uv", "run", "python", "app.py"]
