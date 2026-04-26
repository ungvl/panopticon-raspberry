```
....................................................................................................
....................................................................................................
....................................................................................................
...........................................              ...........................................
...................................                              ...................................
...............................                                      ...............................
............................               #@@@@@@@@@@@@#               ............................
.........................               @@@@@@@@@@@@@@@@@@@@               .........................
.......................               @@@@@@@@@@@@@@@@..@@@@@@              ........................
......................              =@@@@@@@@@@@@@@@@.  -@@@@@@-              ......................
.....................              @@@@@@@@@@@@@@@@@@@@@@@@@@@@@%              .....................
....................              =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-              ....................
...................               @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               ...................
...................              -@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:              ...................
...................              #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#              ...................
...................              *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*              ...................
...................              *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*              ...................
...................               @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               ...................
....................              @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@              ....................
....................               @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@              .....................
......................              @@@@@@@@@@@@@@@@@@@@@@@@@@              ......................
.......................              @@@@@@@@@@@@@@@@@@@@@@@@@@              .......................
.........................              @@@@@@@@@@@@@@@@@@@@@@              .........................
...........................              *@@@@@@@@@@@@@@@@*              ...........................
..............................               -@@@@@@@@-               ..............................
..................................                                ..................................
.........................................                  .........................................
....................................................................................................
....................................................................................................
....................................................................................................

 ____                        _   _                 
|  _ \ __ _ _ __   ___  _ __| |_(_) ___ ___  _ __  
| |_) / _` | '_ \ / _ \| '_ \ __| |/ __/ _ \| '_ \ 
|  __/ (_| | | | | (_) | |_) | |_| | (_| (_) | | | |
|_|   \__,_|_| |_|\___/| .__/ \__|_|\___\___/|_| |_|
                       |_|                          
```

# Panopticon Raspberry Pi - Activity & Face Tracker

A comprehensive tracking solution using ActivityWatch for screen tracking and InsightFace for face recognition, designed for Raspberry Pi.

> [!IMPORTANT]
> **Zero-Image Architecture**: This system uses a privacy-first approach. No facial images are stored on the device or disk. All face embeddings are strictly loaded from RAM via secure Cloud Sync.

## Features
- **Screen Tracking**: Tracks active window title and application using ActivityWatch.
- **Face Recognition**: Detects and identifies faces using InsightFace (RAM-only).
- **Scale / Weight Tracking**: Reads weight from an HX711 load cell and logs changes.
- **Cloud Sync**: Fetches encrypted user identities directly from **Appwrite**.
- **Privacy by Design**: No local database or image storage.

## Project Structure
```
panopticon-raspberry/
├── src/                        # Source code
│   ├── screen_tracker.py       # ActivityWatch integration
│   ├── face_tracker.py         # Face recognition logic (RAM-only)
│   ├── face_logger.py          # Orchestrator & Cloud Sync
│   ├── scale.py                # HX711 scale reader
│   ├── scale_calibration.py    # Interactive scale calibration wizard
│   ├── db_connector.py         # Appwrite Cloud Handler
│   ├── clock.py                # LCD clock display
│   └── start_aw.py             # Main entry point
├── activitywatch/              # ActivityWatch submodules
├── scale_calibration.json      # Scale calibration values (generated, git-ignored)
├── setup.sh                    # Setup script
├── requirements.txt            # Python dependencies
└── README.md
```

## Deployment on Raspberry Pi

### Prerequisites
- Raspberry Pi (4 or 5 recommended for better face tracking performance)
- Camera (USB or Pi Camera)
- Python 3.7+
- Git

### Quick Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ungvl/panopticon-raspberry.git
    cd panopticon-raspberry
    ```

2.  **Run the setup script**:
    The setup script will install system dependencies, initialize submodules, create a virtual environment, and install all Python packages.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3.  **Configuration (.env)**:
    Create a `.env` file in the root directory with your Appwrite credentials.
    
    ```ini
    APPWRITE_ENDPOINT="https://cloud.appwrite.io/v1"
    APPWRITE_PROJECT_ID="your_project_id"
    APPWRITE_API_KEY="your_api_key"
    APPWRITE_DATABASE_ID="your_database_id"
    APPWRITE_USERS_COLLECTION_ID="your_users_collection_id"
    ```

### Running the Tracker

**Linux / Raspberry Pi**:
```bash
./run.sh
```

> [!NOTE]
> **First Run**: On the first start, the system will download approximately 200MB of AI models. This may take a few minutes.

**Windows**:  
```bash
run.bat
```

To stop, press `Ctrl+C` in the terminal.

## Data Architecture

### Cloud Sync (Startup)
1.  System boots.
2.  `face_logger` calls `db_connector.sync_known_faces()`.
3.  Connects to Appwrite using `APPWRITE_API_KEY`.
4.  Fetches user list + **512-dim Face Embeddings**.
5.  Injects embeddings directly into `FaceTracker` RAM.
6.  *No images are ever saved to disk.*

### Event Logging
- **Screen Events**: Pushed to Appwrite via ActivityWatch integration.
- **Face Events**: Pushed to Appwrite Face Receiver function.
- **Weight Events**: Pushed to Appwrite Weight Receiver function (if configured).

## Scale (HX711 Load Cell)

The scale module reads weight from a load cell connected via an HX711 amplifier.

### Wiring

| HX711 Pin | Raspberry Pi Pin |
|-----------|-----------------|
| VCC | 3.3V or 5V |
| GND | GND |
| DT (DOUT) | GPIO 5 (default, configurable via `HX711_DT_PIN`) |
| SCK | GPIO 6 (default, configurable via `HX711_SCK_PIN`) |

### Installation

Install the `hx711py` library:
```bash
sudo apt-get install git
sudo git clone https://github.com/j-dohnalek/hx711py
cd hx711py
sudo python3 setup.py install
```

### Calibration

> [!IMPORTANT]
> Calibration is **required** before the scale can return meaningful weight values. Without it, readings will be raw sensor data.

Run the interactive calibration wizard:
```bash
sudo python3 -m src.scale_calibration
```

The wizard walks through 3 steps:
1. **Offset** — reads the empty scale to get the zero-point value.
2. **Ratio** — you place a known weight (e.g. 500g) and the script calculates the conversion ratio: `ratio = (raw_reading - offset) / known_weight`.
3. **Verify** — takes 5 test readings for you to confirm accuracy.

Calibration values are saved to `scale_calibration.json`. You can also set them via `.env`:
```ini
HX711_OFFSET=12345.67
HX711_RATIO=420.50
```

### Scale Configuration (.env)

```ini
# GPIO pins (optional, defaults shown)
HX711_DT_PIN=5
HX711_SCK_PIN=6

# Reading behavior
SCALE_READ_INTERVAL=2.0           # Seconds between reads
SCALE_CHANGE_THRESHOLD=5.0        # Min grams change to trigger a log
SCALE_HEARTBEAT_INTERVAL=60.0     # Force log every N seconds even if stable

# Appwrite endpoint (optional — without this, weight is logged locally only)
APPWRITE_WEIGHT_FUNCTION_URL=https://your-function-id.fra.appwrite.run/
```

## Troubleshooting

### Camera Issues
- Ensure the camera is connected and enabled in `raspi-config`.
- If using the Legacy camera stack, ensure it is enabled.
- For `libcamera`, you might need `libcameradev` dependencies.

### Performance
- If face tracking is slow, ensure you're using a Pi 4/5. 
- The system is optimized with `det_size=(160, 160)` for faster inference.

### Missing Libraries
- The `setup.sh` installs most common libraries. If you see `ImportError: lib...so.X`, try running:
  `sudo apt install libopenblas-dev libopenjp2-7-dev`

### Wayland & Window Tracking
If you see `[WARNING]: Code made an unclear branch` in the logs:
- **What it means**: The new Raspberry Pi OS uses "Wayland," which restricts applications from seeing each other's window titles for security.
- **Is it a problem?**: No, it's a non-fatal warning. The watcher will still try to capture events.
- **How to fix**: To get perfect window titles, you can switch your Pi to the "X11" backend using `raspi-config` (Advanced Options -> Wayland -> X11).
