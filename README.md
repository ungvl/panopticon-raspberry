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
...................               @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               ...................
....................              @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@              ....................
....................               @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@              .....................
......................              @@@@@@@@@@@@@@@@@@@@@@@@@@@@              ......................
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

## Features
- **Screen Tracking**: Tracks active window title and application using ActivityWatch.
- **Face Recognition**: Detects and identifies faces using InsightFace.
- **Database Storage**: All events stored in SQLite (configurable).
- **Easy Setup**: Configuration wizard on first run.

## Project Structure
```
panopticon-raspberry/
├── src/                    # Source code
│   ├── screen_tracker.py   # ActivityWatch integration
│   ├── face_tracker.py     # Face recognition logic
│   ├── face_logger.py      # Face tracking DB integration
│   ├── db_connector.py     # Database handler
│   ├── start_aw.py         # Main entry point
│   ├── config_wizard.py    # Configuration GUI
│   ├── verify_db.py        # Database verification tool
│   └── known_faces/        # Face images for recognition (gitignored)
├── activitywatch/          # ActivityWatch source (gitignored)
├── setup.sh                # Setup script
├── requirements.txt        # Python dependencies
└── README.md
```

## Deployment on Raspberry Pi

### Prerequisites
- Python 3.7+
- Git
- Camera (for face tracking)

### Installation

1.  **Clone the repository with submodules**:
    ```bash
    git clone --recurse-submodules <repository_url>
    cd panopticon-raspberry
    ```
    
    *If you already cloned without submodules:*
    ```bash
    git submodule update --init --recursive
    ```

2.  **Run the setup script**:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
    
    The script will:
    - Create a Python virtual environment
    - Install all dependencies
    - Install ActivityWatch from the local `activitywatch/` directory
    
    *Note: You may need to install `python3-tk` if the GUI wizard fails:*
    ```bash
    sudo apt install python3-tk
    ```

3.  **Add known faces** (optional):
    - Create `src/known_faces/` directory if it doesn't exist
    - Add face images named `PersonName.jpg` (e.g., `John.jpg`, `Jane.jpg`)
    - Images should contain a clear, frontal face

4.  **Start the tracker**:
    ```bash
    source venv/bin/activate
    python -m src.start_aw
    ```

5.  **Configuration**:
    - On the first run, a popup will ask for the Database Connection String
    - Leave it empty to use the default local SQLite database (`activity_data.db`)
    - To change it later, edit the `.env` file directly

## Usage

### Verify Data Collection
Check the database to see collected events:
```bash
source venv/bin/activate
python src/verify_db.py
```

### Stop the Tracker
Press `Ctrl+C` in the terminal where the tracker is running.

## Development

### Local Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install ActivityWatch from local directory
pip install ./activitywatch/aw-core
pip install ./activitywatch/aw-client
pip install ./activitywatch/aw-server
pip install ./activitywatch/aw-watcher-window

# Run
python -m src.start_aw
```

## Database Schema

### screen_events
- `id` (INTEGER): Primary key
- `timestamp` (TEXT): ISO format timestamp
- `app` (TEXT): Application name
- `title` (TEXT): Window title
- `duration` (REAL): Duration in seconds

### face_events
- `id` (INTEGER): Primary key
- `timestamp` (TEXT): ISO format timestamp
- `name` (TEXT): Detected person name or "Unknown"
- `confidence` (REAL): Recognition confidence (0.0-1.0)

## Troubleshooting

### Face tracker not detecting faces
- Ensure camera is connected and accessible
- Check that `insightface` models are downloaded (happens automatically on first run)
- Verify face images in `src/known_faces/` are clear and frontal

### Screen tracker not working
- Ensure ActivityWatch components installed correctly
- Check that `aw-server` and `aw-watcher-window` are running

### Configuration wizard not appearing
- Install `python3-tk`: `sudo apt install python3-tk`
- Manually create `.env` file with: `DB_CONNECTION_STRING=sqlite:///activity_data.db`
