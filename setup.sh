#!/bin/bash

# Exit on error
set -e

echo "[INFO] Starting Panopticon Setup for Raspberry Pi..."

# Check for python3 and venv
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install it: sudo apt install python3"
     exit 1
fi

# Check for internet connectivity
echo "[INFO] Checking internet connectivity..."
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo "[WARNING] Could not reach 8.8.8.8. You might have internet issues."
    echo "[INFO] Note: If you are behind a proxy, ensure HTTP_PROXY is set."
fi

# Check if ActivityWatch submodules are present
if [ ! -f "activitywatch/aw-server/pyproject.toml" ]; then
    echo "[WARNING] ActivityWatch submodules seem to be missing!"
    echo "[INFO] Attempting to initialize submodules..."
    
    # Check if we are in a git repository
    if [ ! -d ".git" ]; then
        echo "[ERROR] This directory is not a git repository. Cannot auto-pull submodules."
        echo "[INFO] Please clone the repository properly using: "
        echo "       git clone --recurse-submodules https://github.com/ungvl/panopticon-raspberry.git"
        exit 1
    fi

    echo "[INFO] Running: git submodule update --init --recursive"
    if git submodule update --init --recursive; then
        echo "[INFO] Submodules initialized via root."
    else
        echo "[WARNING] Submodule update failed. Trying alternative methods..."
        
        # Method 2: Try to fix the index (sometimes needed if files exist but submodules don't)
        git submodule init &> /dev/null || true
        git submodule update --recursive &> /dev/null || true

        # Method 3: Direct Clone Fallback (The Nuclear Option)
        if [ ! -f "activitywatch/aw-server/pyproject.toml" ]; then
            echo "[INFO] Submodule system failing. Attempting a direct clone of ActivityWatch..."
            
            # Backup existing directory if it's not empty/working
            if [ -d "activitywatch" ] && [ "$(ls -A activitywatch)" ]; then
                echo "[INFO] Moving existing activitywatch directory to backup..."
                mv activitywatch activitywatch_backup_$(date +%s)
            fi

            mkdir -p activitywatch
            git clone --recursive https://github.com/ActivityWatch/activitywatch.git activitywatch
        fi
    fi

    # Final verification
    if [ ! -f "activitywatch/aw-server/pyproject.toml" ]; then
        echo "[ERROR] ActivityWatch files are still missing."
        echo "[INFO] Please manually run: "
        echo "       git clone --recursive https://github.com/ActivityWatch/activitywatch.git activitywatch"
        exit 1
    fi
    echo "[INFO] ActivityWatch dependencies verified."
fi

# Install system dependencies for OpenCV and InsightFace on Raspberry Pi
echo "[INFO] Installing system dependencies (requires sudo)..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    libopenjp2-7-dev \
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
echo "[INFO] Note: On the first run, the system will download ~200MB of AI models."
echo "[INFO]       This may take a few minutes depending on your internet speed."
