#!/bin/bash

# Configuration
VENV_DIR=".venv"                  # Virtual environment directory
REQUIREMENTS="requirements.txt"  # File with dependencies
PYTHON_SCRIPT="api.py"           # Your Python script
LOG_FILE="app.log"               # Log file

# Environment variables (you can add your own)
export TELEGRAM_TOKEN=""
export TELEGRAM_CHAT_ID=""
export PORT="500"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if requirements.txt exists
if [ -f "$REQUIREMENTS" ]; then
    echo "Installing dependencies..."
    pip install -r "$REQUIREMENTS"
fi

# Start Python script in background with logging
echo "Starting Python script in background..."
nohup python "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
echo "PID: $!"
