#!/bin/zsh

IMAGE_NAME="ben-app"

echo "Building Docker image ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" .

if [ $? -eq 0 ]; then
  echo "Docker image ${IMAGE_NAME} built successfully."
else
  echo "Failed to build Docker image ${IMAGE_NAME}."
  exit 1
fi
