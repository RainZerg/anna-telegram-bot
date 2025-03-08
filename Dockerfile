# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# First, create necessary directories
RUN mkdir -p /app/media
RUN mkdir -p /app/data

# Copy all application files
COPY . /app/

# Explicitly verify and copy media files
RUN echo "Contents of /app/media after COPY:" && ls -la /app/media

# Ensure media directory has correct permissions
RUN chmod -R 755 /app/media

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Add an entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
