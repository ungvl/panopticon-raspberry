# Panopticon Raspberry Pi Screen Tracker

A screen tracking solution using ActivityWatch, designed for Raspberry Pi.

## Features
- Tracks active window title and application.
- Stores data in a SQLite database (configurable).
- Easy setup with a configuration wizard.

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

3.  **Start the tracker**:
    ```bash
    source venv/bin/activate
    python start_aw.py
    ```

4.  **Configuration**:
    - On the first run, a popup will ask for the Database Connection String.
    - Leave it empty to use the default local SQLite database (`activity_data.db`).
    - To change it later, edit the `.env` file directly.

## Development

- Install dependencies: `pip install -r requirements.txt`
- Run: `python start_aw.py`
