#!/bin/bash

set -e  # Exit on any error

echo "Starting Docker entrypoint script..."

# Check if SERVICE_DIR environment variable is set
if [ -z "$SERVICE_DIR" ]; then
    echo "Error: SERVICE_DIR environment variable is not set"
    echo "Available services:"
    ls -la /app/services/
    exit 1
fi

echo "SERVICE_DIR is set to: $SERVICE_DIR"

# Check if the service directory exists
SERVICE_PATH="/app/services/$SERVICE_DIR"
if [ ! -d "$SERVICE_PATH" ]; then
    echo "Error: Service directory $SERVICE_PATH does not exist"
    echo "Available services:"
    ls -la /app/services/
    exit 1
fi

echo "Service directory found: $SERVICE_PATH"

# Check if app.py exists in the service directory
if [ ! -f "$SERVICE_PATH/app.py" ]; then
    echo "Error: app.py not found in $SERVICE_PATH"
    echo "Contents of $SERVICE_PATH:"
    ls -la "$SERVICE_PATH"
    exit 1
fi

echo "app.py found in service directory"

# Change to service directory
cd "$SERVICE_PATH"
echo "Changed to directory: $(pwd)"

# Install requirements if they exist
if [ -f "requirements.txt" ]; then
    echo "Installing requirements for $SERVICE_DIR..."
    pip install -r requirements.txt
    echo "Requirements installed successfully"
else
    echo "No requirements.txt found, skipping dependency installation"
fi

# Set default PORT if not provided
export PORT=${PORT:-10000}
echo "Starting Flask application on port $PORT..."

# Run the Flask application
exec python app.py