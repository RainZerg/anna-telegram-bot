#!/bin/bash

# Ensure directories exist
mkdir -p media
mkdir -p data

# Check if cover image exists in media directory
if [ ! -f media/cover_image.jpg ]; then
    echo "Warning: cover_image.jpg not found in media directory!"
    echo "Please ensure cover_image.jpg is present in the media directory."
    exit 1
fi

# Stop any running containers
docker compose down

# Rebuild without cache
docker compose build --no-cache

# Start the containers
docker compose up -d

# Show the logs
docker compose logs -f
