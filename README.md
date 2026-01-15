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
- Python 3.7+
- Git
- Camera (for face tracking)
- **Appwrite Cloud Account** (Project ID, API Key, Database)

### Installation

1.  **Clone the repository with submodules**:
    ```bash
    git clone --recurse-submodules <repository_url>
    cd panopticon-raspberry
    ```

2.  **Run the setup script**:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3.  **Configuration (.env)**:
    Create a `.env` file in the root directory with your Appwrite credentials.
    > [!WARNING]
    > The **API Key** is required to fetch the restricted "Users" collection containing biometric data. Keep this file secure.
    
    ```ini
    APPWRITE_ENDPOINT="https://cloud.appwrite.io/v1"
    APPWRITE_PROJECT_ID="your_project_id"
    APPWRITE_API_KEY="your_api_key_with_users_read_access"
    APPWRITE_DATABASE_ID="your_database_id"
    APPWRITE_USERS_COLLECTION_ID="your_users_collection_id"
    ```

### Running the Tracker

**Windows**:  
Double-click `run.bat`.

**Linux / Raspberry Pi**:
```bash
source venv/bin/activate
python -m src.start_aw
```

To stop, press `Ctrl+C`.

## Data Architecture

### Cloud Sync (Startup)
1.  System boots.
2.  `face_logger` calls `db_connector.sync_known_faces()`.
3.  Connects to Appwrite using `APPWRITE_API_KEY`.
4.  Fetches user list + **512-dim Face Embeddings**.
5.  Injects embeddings directly into `FaceTracker` RAM.
6.  *No images are ever saved to disk.*

### Event Logging
- **Screen Events**: Pushed to Appwrite Function A.
- **Face Events**: Pushed to Appwrite Function B (Face Receiver).

## Troubleshooting

### Face tracker not detecting anyone (Unknown)
- Check `.env` credentials.
- Ensure the API Key has `read` permissions for the Users collection.
- Verify that users in Appwrite have a valid `face_embedding` field (array of 512 floats).

### Screen tracker not working
- Ensure `aw-server` is running (started automatically by `start_aw.py`).
- Check logs for "Connected to ActivityWatch".
