#!/bin/zsh

CONTAINER_NAME="ben-app-container"
IMAGE_NAME="ben-app"
DB_VOLUME_NAME="ben_db_data"

# Stop and remove existing container with the same name, if it exists
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "Stopping existing container ${CONTAINER_NAME}..."
    docker stop "${CONTAINER_NAME}"
fi

if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "Removing existing container ${CONTAINER_NAME}..."
    docker rm "${CONTAINER_NAME}"
fi

# Create a named volume for the database if it doesn't already exist
if ! docker volume inspect "${DB_VOLUME_NAME}" &>/dev/null; then
    echo "Creating Docker volume ${DB_VOLUME_NAME} for database persistence..."
    docker volume create "${DB_VOLUME_NAME}"
fi

echo "Running Docker container ${CONTAINER_NAME} from image ${IMAGE_NAME}..."
docker run -d \
    -p 5000:5000 \
    -v "${DB_VOLUME_NAME}:/app" \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    "${IMAGE_NAME}"

if [ $? -eq 0 ]; then
  echo "Docker container ${CONTAINER_NAME} started successfully and configured to restart automatically."
  echo "Access the application at http://localhost:5000"
else
  echo "Failed to start Docker container ${CONTAINER_NAME}."
  exit 1
fi
