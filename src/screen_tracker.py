import time
import logging
import os
import sys
from aw_core.models import Event
from aw_client import ActivityWatchClient
from .db_connector import DatabaseConnector

# Import Xlib for native tracking
try:
    import Xlib
    import Xlib.display
    from Xlib import X
except ImportError:
    logging.error("python-xlib is not installed. Native tracking will fail.")
    Xlib = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_native_window_info(display):
    if not display:
        return None, None
        
    try:
        screen = display.screen()
        root = screen.root
        
        # Check Active Window property (EWMH standard)
        NET_ACTIVE_WINDOW = display.intern_atom("_NET_ACTIVE_WINDOW")
        prop = root.get_full_property(NET_ACTIVE_WINDOW, X.AnyPropertyType)
        
        if not prop:
            return "unknown", "unknown"
            
        window_id = prop.value[0]
        if window_id == 0:
            return "unknown", "unknown"
            
        window = display.create_resource_object("window", window_id)
        
        # Get Class
        cls_tuple = window.get_wm_class()
        cls = cls_tuple[1] if cls_tuple else "unknown"
        
        # Get Name
        name = window.get_wm_name()
        
        # Fallback for name if it's bytes
        if isinstance(name, bytes):
            name = name.decode('utf-8', 'ignore')
        if not name:
            name = "unknown"
            
        return cls, name
    except Exception as e:
        logging.debug(f"Error getting native window info: {e}")
        return "unknown", "unknown"

def main():
    # Initialize Database Connector
    db = DatabaseConnector()

    # Initialize X11 Display
    display = None
    if Xlib:
        try:
            display = Xlib.display.Display()
            logging.info("Native X11 display connection established.")
        except Exception as e:
            logging.error(f"Failed to connect to X11 display: {e}")

    # Initialize ActivityWatch Client with retry logic
    client_name = "panopticon-screen-tracker"
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
    
    bucket_id = f"{client_name}_window"
    logging.info(f"Tracking active window directly via X11...")

    last_app = None
    last_title = None
    start_time = time.time()

    try:
        while True:
            app, title = get_native_window_info(display)
            
            # Simple change detection
            if app != last_app or title != last_title:
                now = time.time()
                duration = now - start_time
                
                # Log previous event if it lasted more than 1s
                if last_app and duration > 0.1:
                    db_data = {
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
                        "app": last_app,
                        "title": last_title,
                        "duration": round(duration, 2)
                    }
                    logging.info(f"Activity: {last_app} - {last_title} ({round(duration, 1)}s)")
                    db.send_data(db_data)
                    
                    # Also log to ActivityWatch
                    event = Event(timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)), 
                                 duration=duration, 
                                 data={"app": last_app, "title": last_title})
                    aw.heartbeat(bucket_id, event, pulsetime=10)

                # Reset for new event
                last_app = app
                last_title = title
                start_time = now
            
            time.sleep(1) # Poll every second

    except KeyboardInterrupt:
        logging.info("Stopping screen tracker...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
