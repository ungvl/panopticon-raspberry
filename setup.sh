#!/bin/bash

# Exit on error
set -e

echo "[INFO] Starting Panopticon Setup for Raspberry Pi..."

# Check for python3 and venv
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install it: sudo apt install python3"
     exit 1
fi

# Install system dependencies for OpenCV and InsightFace on Raspberry Pi
echo "[INFO] Installing system dependencies (requires sudo)..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    libatlas-base-dev \
    libjasper-dev \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5 \
    libhdf5-dev \
    libilmbase-dev \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    python3-tk

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "[INFO] Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "[INFO] requirements.txt not found, installing base dependencies manually..."
    pip install python-dotenv insightface opencv-python onnxruntime requests numpy
fi

# Install ActivityWatch components from local directory
echo "[INFO] Installing ActivityWatch from local directory..."
if [ -d "activitywatch" ]; then
    # We need to install these in order
    echo "[INFO] Installing aw-core..."
    pip install ./activitywatch/aw-core
    echo "[INFO] Installing aw-client..."
    pip install ./activitywatch/aw-client
    echo "[INFO] Installing aw-server..."
    pip install ./activitywatch/aw-server
    echo "[INFO] Installing aw-watcher-window..."
    pip install ./activitywatch/aw-watcher-window
else
    echo "[ERROR] activitywatch directory not found!"
    echo "[INFO] Please ensure the activitywatch submodule is cloned with: git submodule update --init --recursive"
    exit 1
fi

# Create a run.sh script for convenience
echo "[INFO] Creating run.sh script..."
cat <<EOF > run.sh
#!/bin/bash
source venv/bin/activate
echo "[INFO] Starting Panopticon..."
python3 -m src.start_aw
EOF
chmod +x run.sh

echo ""
echo "[INFO] Setup complete!"
echo "[INFO] To start the tracker, run: ./run.sh"
echo "[INFO] Note: Make sure your .env file is configured."
