#!/bin/bash

# Lock script directory to ensure relative paths work reliably
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
VENV_DIR="$SCRIPT_DIR/.venv"    # Path to virtual environment
REQUIREMENTS="requirements.txt" # File with Python dependencies
PYTHON_SCRIPT="api.py"          # Main Python script to run
LOG_FILE="app.log"              # File for background logs

# Environment variables (can be extended if needed)
export TELEGRAM_TOKEN=""
export TELEGRAM_CHAT_ID=""
export PORT="5000"

# Function to locate pip or pip3
get_pip() {
    if command -v pip >/dev/null 2>&1; then
        echo "pip"
    elif command -v pip3 >/dev/null 2>&1; then
        echo "pip3"
    else
        echo "Error: pip or pip3 not found!" >&2
        exit 1
    fi
}

PIP_CMD=$(get_pip)

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "❌ Failed to create virtual environment" >&2
        exit 1
    fi
else
    echo "✅ Virtual environment already exists."
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if requirements.txt is present
if [ -f "$REQUIREMENTS" ]; then
    echo "Installing dependencies from $REQUIREMENTS..."
    if ! $PIP_CMD install -r "$REQUIREMENTS"; then
        echo "❌ Failed to install dependencies." >&2
        exit 1
    fi
else
    echo "⚠️ No $REQUIREMENTS file found. Skipping installation."
fi

# Start the Python script in the background with log redirection
echo "🚀 Starting $PYTHON_SCRIPT in background..."
nohup python "$PYTHON_SCRIPT" >"$LOG_FILE" 2>&1 &
echo "🆗 Started with PID $!"
