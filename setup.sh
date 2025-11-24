#!/bin/bash

# Exit on error
set -e

echo "[INFO] Starting Panopticon Setup..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install it."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install base dependencies first
echo "[INFO] Installing base dependencies..."
pip install python-dotenv insightface opencv-python onnxruntime

# Install ActivityWatch components from local directory
echo "[INFO] Installing ActivityWatch from local directory..."
if [ -d "activitywatch" ]; then
    pip install ./activitywatch/aw-core
    pip install ./activitywatch/aw-client
    pip install ./activitywatch/aw-server
    pip install ./activitywatch/aw-watcher-window
else
    echo "[ERROR] activitywatch directory not found!"
    echo "[INFO] Please ensure the activitywatch submodule is cloned."
    exit 1
fi

# Install system dependencies for tkinter (might be needed on some Linux distros)
echo "[INFO] Note: You might need to install 'python3-tk' via apt if the GUI config wizard fails."
echo "[INFO] Run: sudo apt install python3-tk"

echo ""
echo "[INFO] Setup complete!"
echo "[INFO] To start the tracker:"
echo "  1. source venv/bin/activate"
echo "  2. python -m src.start_aw"
