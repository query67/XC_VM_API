#!/bin/bash

# Lock script directory to ensure relative paths work reliably
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
VENV_DIR="$SCRIPT_DIR/.venv"    # Path to virtual environment
REQUIREMENTS="requirements.txt" # File with Python dependencies
PYTHON_SCRIPT="api.py"          # Main Python script to run
LOG_FILE="app.log"              # File for background logs
PID_FILE="app.pid"              # File to store process PID

# Function to stop existing process
stop_existing_process() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "🛑 Stopping existing process (PID: $OLD_PID)..."
            kill -9 $OLD_PID
            sleep 1 # Give time for process to terminate
        else
            echo "ℹ️ No running process found for PID $OLD_PID"
        fi
        rm -f "$PID_FILE"
    fi
}

# Stop existing process before setup
stop_existing_process

# Ask user about Git update
read -p "Do you want to update from Git? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Updating code from Git..."
    if git pull; then
        echo "✅ Git update successful"
    else
        echo "❌ Git update failed! Continuing with existing code."
    fi
else
    echo "⏩ Skipping Git update"
fi

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
    if ! python3 -m pip install --upgrade pip wheel || ! python3 -m pip install -r "$REQUIREMENTS"; then
        echo "❌ Failed to install dependencies." >&2
        exit 1
    fi
else
    echo "⚠️ No $REQUIREMENTS file found. Skipping installation."
fi

# Start the Python script in the background with log redirection
echo "🚀 Starting $PYTHON_SCRIPT in background..."
nohup python3 "$PYTHON_SCRIPT" >"$LOG_FILE" 2>&1 &

# Get and store PID
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"
echo "🆗 Started with PID $NEW_PID (PID saved to $PID_FILE)"