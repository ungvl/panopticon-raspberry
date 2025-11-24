import time
import logging
from datetime import datetime, timezone
from .db_connector import DatabaseConnector
from .face_tracker import FaceTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FaceLogger:
    def __init__(self):
        self.db = DatabaseConnector()
        self.tracker = FaceTracker(known_faces_dir="src/known_faces")
        self.last_logged = {} # {name: timestamp}
        self.log_interval = 5.0 # Seconds between logs for the same face

    def handle_faces(self, faces):
        now = time.time()
        for face in faces:
            name = face['name']
            confidence = face['confidence']
            
            # Rate limiting
            if name in self.last_logged:
                if now - self.last_logged[name] < self.log_interval:
                    continue
            
            self.last_logged[name] = now
            
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": name,
                "confidence": confidence
            }
            
            logging.info(f"Detected: {name} ({confidence:.2f})")
            self.db.send_face_data(data)

    def start(self):
        logging.info("Starting Face Logger...")
        # Check if we are in a headless environment (optional logic could go here)
        # For now, we assume we might want to see the window if connected to a screen
        # But on a Pi over SSH, we might want show_window=False
        # Let's default to True for now, user can change or we can detect DISPLAY env var
        
        import os
        show_window = True
        if os.name == 'posix' and 'DISPLAY' not in os.environ:
             show_window = False
             logging.info("Headless mode detected (no DISPLAY). Disabling video window.")

        self.tracker.start(callback=self.handle_faces, show_window=show_window)

if __name__ == "__main__":
    logger = FaceLogger()
    logger.start()
