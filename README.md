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
│   └── known_faces/        # Face images for recognition (gitignored)
├── activitywatch/          # ActivityWatch source (gitignored)
├── setup.sh                # Setup script
├── requirements.txt        # Python dependencies
└── README.md
```

## Deployment on Raspberry Pi

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd panopticon-raspberry
    ```

2.  **Run the setup script**:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
    *Note: You may need to install `python3-tk` if the GUI wizard fails (`sudo apt install python3-tk`).*

3.  **Add known faces** (optional):
    - Create `src/known_faces/` directory
    - Add face images named `PersonName.jpg` (e.g., `John.jpg`, `Jane.jpg`)

4.  **Start the tracker**:
    ```bash
    source venv/bin/activate
    python -m src.start_aw
    ```

5.  **Configuration**:
    - On the first run, a popup will ask for the Database Connection String.
    - Leave it empty to use the default local SQLite database (`activity_data.db`).
    - To change it later, edit the `.env` file directly.

## Development

- Install dependencies: `pip install -r requirements.txt`
- Run: `python -m src.start_aw`
- View ActivityWatch UI: http://localhost:5600

## Database Schema

### screen_events
- `id`, `timestamp`, `app`, `title`, `duration`

### face_events
- `id`, `timestamp`, `name`, `confidence`
