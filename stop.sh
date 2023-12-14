#!/bin/bash

# Check if the container is running
if [ ! "$(docker ps -q -f name=blob-api-container)" ]; then
    echo "No such running container."
    exit 1
fi

# Stop the container
docker stop blob-api-container
