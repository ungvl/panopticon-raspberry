import time
import logging
from aw_core.models import Event
from aw_client import ActivityWatchClient
from .db_connector import DatabaseConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize Database Connector
    db = DatabaseConnector()

    # Initialize ActivityWatch Client with retry logic
    client_name = "aw-watcher-screen-tracker"
    aw = None
    
    logging.info("Connecting to ActivityWatch...")
    while aw is None:
        try:
            aw = ActivityWatchClient(client_name, testing=False)
            bucket_id = f"{client_name}_window"
            event_type = "currentwindow"
            aw.create_bucket(bucket_id, event_type=event_type, queued=True)
            logging.info(f"Connected to ActivityWatch. Bucket: {bucket_id}")
        except Exception as e:
            logging.warning(f"Could not connect to ActivityWatch ({e}). Retrying in 5s...")
            time.sleep(5)

    # Poll for the latest window event from the standard aw-watcher-window bucket
    # We assume aw-watcher-window is running and logging to 'aw-watcher-window_{hostname}'
    
    hostname = aw.client_hostname
    window_bucket_id = f"aw-watcher-window_{hostname}"
    
    logging.info(f"Listening for events from: {window_bucket_id}")

    last_event_id = None

    try:
        while True:
            # Get the last event from the window bucket
            try:
                events = aw.get_events(window_bucket_id, limit=1)
            except Exception as e:
                logging.error(f"Failed to get events: {e}")
                time.sleep(5)
                continue
            
            if events:
                event = events[0]
                if event.id != last_event_id:
                    # New event detected
                    last_event_id = event.id
                    data = event.data
                    
                    # Format data for DB
                    db_data = {
                        "timestamp": event.timestamp.isoformat(),
                        "app": data.get("app"),
                        "title": data.get("title"),
                        "duration": event.duration.total_seconds()
                    }
                    
                    logging.info(f"New Window Event: {db_data['app']} - {db_data['title']}")
                    db.send_data(db_data)
            
            time.sleep(1) # Poll every second

    except KeyboardInterrupt:
        logging.info("Stopping screen tracker...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
