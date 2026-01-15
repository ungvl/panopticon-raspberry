import cv2
import time
import threading
import numpy as np
from insightface.app import FaceAnalysis

class FaceTracker:
    def __init__(self, known_faces=None, sim_threshold=0.4):
        """
        :param known_faces: List of dicts [{'name': '...', 'id': '...', 'embedding': np.array}, ...]
        :param sim_threshold: Cosine similarity threshold for matching.
        """
        self.sim_threshold = sim_threshold
        self.app = FaceAnalysis(name="buffalo_s")
        self.app.prepare(ctx_id=-1, det_size=(160, 160)) # Pi optimization
        
        # Zero-Image Architecture: Load embeddings from memory only
        self.known_embeddings = []
        self.known_names = []
        self.known_ids = []

        if known_faces:
             for person in known_faces:
                 self.known_embeddings.append(person['embedding'])
                 self.known_names.append(person['name'])
                 # Store ID if available, defaulting to None
                 self.known_ids.append(person.get('id'))
        
        self.known_embeddings = np.array(self.known_embeddings)
        print(f"[INFO] FaceTracker initialized with {len(self.known_embeddings)} known faces in RAM.")

        self.running = False
        self.cap = None
        self.frame_holder = {"img": None}
        self.results_holder = {"faces": [], "last_run_time": time.time()}
        self.lock = threading.Lock()

    def _cosine_sim_matrix(self, emb, known_embs):
        return np.dot(known_embs, emb)

    def _inference_thread(self):
        while self.running:
            with self.lock:
                img = self.frame_holder["img"]
            
            if img is not None:
                faces = self.app.get(img)
                with self.lock:
                    self.results_holder["faces"] = faces
                    self.results_holder["last_run_time"] = time.time()
            
            time.sleep(0.001)

    def start(self, callback=None, show_window=True):
        """
        Starts the face tracker.
        :param callback: Function to call with detected faces (list of dicts).
        :param show_window: Whether to show the OpenCV window.
        """
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 15)

        self.running = True
        t = threading.Thread(target=self._inference_thread, daemon=True)
        t.start()

        print("[INFO] Face Tracker started.")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("[ERROR] Failed to read frame")
                    break

                with self.lock:
                    self.frame_holder["img"] = frame
                    faces = self.results_holder["faces"]

                detected_faces = []

                for face in faces:
                    x1, y1, x2, y2 = face.bbox.astype(int)
                    label = "Unknown"
                    user_id = None
                    confidence = 0.0

                    if len(self.known_embeddings) > 0:
                        emb = face.normed_embedding.astype("float32")
                        sims = self._cosine_sim_matrix(emb, self.known_embeddings)
                        best_idx = int(np.argmax(sims))
                        best_sim = sims[best_idx]

                        if best_sim > self.sim_threshold:
                            label = self.known_names[best_idx]
                            user_id = self.known_ids[best_idx]
                            confidence = float(best_sim)
                    
                    detected_faces.append({
                        "name": label,
                        "user_id": user_id,
                        "confidence": confidence,
                        "bbox": (x1, y1, x2, y2)
                    })

                    if show_window:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} ({confidence:.2f})", (x1, max(0, y1 - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                if callback and detected_faces:
                    callback(detected_faces)

                if show_window:
                    cv2.imshow("InsightFace Recognition", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                        break
                else:
                    # If no window, just sleep a bit to match FPS
                    time.sleep(1/15)

        except KeyboardInterrupt:
            print("[INFO] Stopping Face Tracker...")
        finally:
            self.running = False
            self.cap.release()
            if show_window:
                cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test run (empty)
    tracker = FaceTracker()
    tracker.start()