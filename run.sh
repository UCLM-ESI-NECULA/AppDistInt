#!/bin/bash

if [ "$(docker ps -q -f name=blob-api-container)" ]; then
    echo "Container is already running."
    exit 1
fi

# Set the default storage folder if not provided in the environment variable
BLOB_STORAGE_FOLDER=${BLOB_STORAGE_FOLDER:-"$PWD/storage"}

# Check if the storage folder exists, create if it does not
if [ ! -d "$BLOB_STORAGE_FOLDER" ]; then
    echo "Storage folder not found. Creating: $BLOB_STORAGE_FOLDER"
    mkdir -p "$BLOB_STORAGE_FOLDER"
fi


# Run the container
docker run --rm --name blob-api-container \
  -p "${BLOB_SERVICE_PORT:-3002}":3002 \
  -v "$BLOB_STORAGE_FOLDER":/data \
  --cpus="1.0" --memory="2g" \
  blob-api-image