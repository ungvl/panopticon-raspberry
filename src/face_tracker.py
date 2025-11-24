import cv2
import os
import time
import threading
import numpy as np
from insightface.app import FaceAnalysis

class FaceTracker:
    def __init__(self, known_faces_dir="src/known_faces", sim_threshold=0.4):
        self.known_faces_dir = known_faces_dir
        self.sim_threshold = sim_threshold
        self.app = FaceAnalysis(name="buffalo_s")
        self.app.prepare(ctx_id=-1, det_size=(160, 160)) # Pi optimization
        self.known_embeddings, self.known_names = self._load_known_faces()
        self.running = False
        self.cap = None
        self.frame_holder = {"img": None}
        self.results_holder = {"faces": [], "last_run_time": time.time()}
        self.lock = threading.Lock()

    def _load_known_faces(self):
        known_embeddings = []
        known_names = []
        
        if not os.path.isdir(self.known_faces_dir):
            print(f"[INFO] No '{self.known_faces_dir}' directory found. Everyone will be 'Unknown'.")
            return np.array([]), []

        for filename in os.listdir(self.known_faces_dir):
            filepath = os.path.join(self.known_faces_dir, filename)
            if not os.path.isfile(filepath): continue

            name, ext = os.path.splitext(filename)
            if ext.lower() not in [".jpg", ".jpeg", ".png"]: continue

            img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"[WARN] Could not read {filepath}, skipping.")
                continue

            faces = self.app.get(img)
            if not faces:
                print(f"[WARN] No face found in {filename}, skipping.")
                continue

            emb = faces[0].normed_embedding 
            known_embeddings.append(emb)
            known_names.append(name)
            print(f"[INFO] Loaded embedding for: {name}")

        return np.array(known_embeddings), known_names

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
        :param callback: Function to call with detected faces (list of dicts with 'name', 'confidence', 'bbox').
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
                    confidence = 0.0

                    if len(self.known_embeddings) > 0:
                        emb = face.normed_embedding.astype("float32")
                        sims = self._cosine_sim_matrix(emb, self.known_embeddings)
                        best_idx = int(np.argmax(sims))
                        best_sim = sims[best_idx]

                        if best_sim > self.sim_threshold:
                            label = self.known_names[best_idx]
                            confidence = float(best_sim)
                    
                    detected_faces.append({
                        "name": label,
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
    # Test run
    tracker = FaceTracker()
    tracker.start()