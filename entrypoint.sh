#!/bin/bash

# Check if the mounted media directory is empty
if [ ! -f /app/media/cover_image.jpg ]; then
    echo "Copying cover image from image to mounted volume..."
    cp -n /app/media_backup/* /app/media/ 2>/dev/null || true
fi

# Start the bot
exec python bot.py
