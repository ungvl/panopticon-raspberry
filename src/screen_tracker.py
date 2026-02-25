import time
import logging
import os
import sys
import traceback

# Configure logging FIRST
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connector
try:
    from src.db_connector import DatabaseConnector
    DB_AVAILABLE = True
except ImportError:
    logging.warning("DatabaseConnector not found. Appwrite logging disabled.")
    DB_AVAILABLE = False

# Xlib for native X11 window tracking
try:
    import Xlib
    import Xlib.display
    from Xlib import X
    XLIB_AVAILABLE = True
except ImportError:
    logging.warning("python-xlib not installed. Native X11 tracking disabled.")
    XLIB_AVAILABLE = False


def get_native_window_info(display):
    """Get the currently focused window's app class and title via X11."""
    if not display:
        return "unknown", "unknown"

    try:
        root = display.screen().root
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
        if isinstance(name, bytes):
            name = name.decode('utf-8', 'ignore')
        if not name:
            name = "unknown"

        return cls, name
    except Exception as e:
        logging.debug(f"X11 query error: {e}")
        return "unknown", "unknown"


def run_tracker():
    logging.info("=" * 50)
    logging.info("PANOPTICON SCREEN TRACKER STARTING")
    logging.info("=" * 50)

    # 1. Database Connector (optional)
    db = None
    if DB_AVAILABLE:
        try:
            db = DatabaseConnector()
            logging.info("DatabaseConnector: OK")
        except Exception as e:
            logging.error(f"DatabaseConnector failed: {e}")

    # 2. X11 Display
    display = None
    if XLIB_AVAILABLE:
        try:
            display = Xlib.display.Display()
            logging.info(f"X11 Display: OK (DISPLAY={os.environ.get('DISPLAY', 'not set')})")
        except Exception as e:
            logging.error(f"X11 Display failed: {e}")

    if not display:
        logging.error("No display connection. Cannot track windows.")
        logging.error("Make sure you are running under X11 and DISPLAY is set.")
        time.sleep(30)
        return

    logging.info("Tracking active window via native X11...")
    logging.info("Screen tracker is RUNNING. You will see logs when you switch windows.")

    last_app = None
    last_title = None
    start_time = time.time()

    while True:
        try:
            app, title = get_native_window_info(display)

            # Change detection
            if app != last_app or title != last_title:
                now = time.time()
                duration = now - start_time

                # Log previous window session (if > 1 second)
                if last_app and duration > 1.0:
                    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))
                    logging.info(f"Activity: {last_app} - {last_title} ({round(duration, 1)}s)")

                    # Send to Appwrite
                    if db:
                        try:
                            db.send_data({
                                "timestamp": ts,
                                "app": last_app,
                                "title": last_title,
                                "duration": round(duration, 2)
                            })
                        except Exception as e:
                            logging.error(f"Appwrite send failed: {e}")

                # Reset for new window
                last_app = app
                last_title = title
                start_time = now

            time.sleep(1)

        except KeyboardInterrupt:
            logging.info("Screen tracker stopped by user.")
            return
        except Exception as e:
            logging.error(f"Tracking loop error: {e}")
            traceback.print_exc()
            time.sleep(2)


def main():
    """Entry point with auto-restart on crash."""
    while True:
        try:
            run_tracker()
        except KeyboardInterrupt:
            logging.info("Stopping screen tracker...")
            break
        except Exception as e:
            logging.error(f"Fatal error: {e}. Restarting in 10s...")
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    main()
