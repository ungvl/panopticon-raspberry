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
- **Cloud Sync**: Fetches encrypted user identities directly from **Appwrite**.
- **Privacy by Design**: No local database or image storage.

## Project Structure
```
panopticon-raspberry/
├── src/                    # Source code
│   ├── screen_tracker.py   # ActivityWatch integration
│   ├── face_tracker.py     # Face recognition logic (RAM-only)
│   ├── face_logger.py      # Orchestrator & Cloud Sync
│   ├── db_connector.py     # Appwrite Cloud Handler
│   └── start_aw.py         # Main entry point
├── activitywatch/          # ActivityWatch submodules
├── setup.sh                # Setup script
├── requirements.txt        # Python dependencies
└── README.md
```

## Deployment on Raspberry Pi

### Prerequisites
- Raspberry Pi (4 or 5 recommended for better face tracking performance)
- Camera (USB or Pi Camera)
- Python 3.7+
- Git

### Quick Setup

1.  **Clone the repository with submodules**:
    ```bash
    git clone --recurse-submodules https://github.com/vladu/panopticon-raspberry.git
    cd panopticon-raspberry
    ```

2.  **Run the setup script**:
    The setup script will install system dependencies, create a virtual environment, and install all Python packages.
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

To start everything (ActivityWatch + Face Tracker):

**Linux / Raspberry Pi**:
```bash
./run.sh
```

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
  `sudo apt install libatlas-base-dev libjasper-dev`
