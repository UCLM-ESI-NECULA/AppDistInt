#!/bin/bash

# Check if the container is already running
if [ "$(docker ps -q -f name=blob-api-container)" ]; then
    echo "Container is already running."
    exit 1
fi

# Use provided port or default to 3002
BLOB_SERVICE_PORT=${1:-3002}

# Use provided storage folder or default to "$PWD/storage"
BLOB_STORAGE_FOLDER="${PWD}/${2:-storage}"

# Check if the storage folder exists, create if it does not
if [ ! -d "$BLOB_STORAGE_FOLDER" ]; then
    echo "Storage folder not found. Creating: ${PWD}/$BLOB_STORAGE_FOLDER"
    mkdir -p "${PWD}/$BLOB_STORAGE_FOLDER"
fi

# Run the Docker container with volume mapping
docker run --rm --name blob-api-container \
  -p "${BLOB_SERVICE_PORT}:3002" \
  -v "$BLOB_STORAGE_FOLDER":/usr/src/app/storage \
  --cpus="1.0" --memory="2g" \
  blob-api-image
