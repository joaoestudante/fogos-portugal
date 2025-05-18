# Stage 1: Build/Setup Environment
FROM python:3.11-slim-bullseye AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install system dependencies if any (e.g., for Pillow, psycopg2-binary, etc.)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir uv

# Copy application code
COPY . .

RUN uv pip install . --system

# Switch to non-root user
USER app



# Expose the port Gunicorn will run on
EXPOSE 5000

# Command to run the application using Gunicorn
# For production, consider adjusting workers based on your server's CPU cores
# CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "server:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "server:app"]