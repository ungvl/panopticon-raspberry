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

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt

# Install system dependencies for tkinter (might be needed on some Linux distros)
# echo "[INFO] You might need to install 'python3-tk' via apt if the GUI fails."

echo "[INFO] Setup complete!"
echo "[INFO] Run 'source venv/bin/activate' then 'python -m src.start_aw' to start."
