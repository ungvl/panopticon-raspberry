import os
import json
import numpy as np
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Appwrite Configuration
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
API_KEY = os.getenv("APPWRITE_API_KEY")
DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("APPWRITE_USERS_COLLECTION_ID")

class DatabaseConnector:
    def __init__(self):
        print(f"[INFO] DatabaseConnector initialized (Appwrite Cloud Sync)")
        if not all([PROJECT_ID, API_KEY, DATABASE_ID, USERS_COLLECTION_ID]):
            print("[WARN] Missing Appwrite environment variables. Sync will fail.")

    def sync_known_faces(self):
        """
        Fetches all registered users from Appwrite Database.
        Parses 'face_embedding' from JSON to NumPy float32 arrays.
        Returns a list of dicts: [{'name': str, 'id': str, 'embedding': np.array}, ...]
        """
        print("[INFO] Syncing known faces from Appwrite...")
        
        headers = {
            "X-Appwrite-Project": PROJECT_ID,
            "X-Appwrite-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        url = f"{APPWRITE_ENDPOINT}/databases/{DATABASE_ID}/collections/{USERS_COLLECTION_ID}/documents"
        
        known_faces = []
        
        try:
            # We assume < 100 users for this Pi implementation. Pagination logic can be added if needed.
            params = {"limit": 100} 
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch users: {response.status_code} {response.text}")
                return []

            data = response.json()
            documents = data.get("documents", [])
            print(f"[INFO] Found {len(documents)} user records.")

            for doc in documents:
                name = doc.get("name", "Unknown")
                user_id = doc.get("$id")
                emb_raw = doc.get("face_embedding") 
                
                # Check for face_embedding_string if that's the field name used
                if not emb_raw:
                     emb_raw = doc.get("face_embedding_string")

                if not emb_raw:
                    print(f"[WARN] User '{name}' has no embedding. Skipping.")
                    continue

                try:
                    # Depending on how it's stored, it might be a JSON string or a list object
                    if isinstance(emb_raw, str):
                        emb_list = json.loads(emb_raw)
                    else:
                        emb_list = emb_raw

                    if not isinstance(emb_list, list) or len(emb_list) != 512:
                        print(f"[WARN] Invalid embedding format for '{name}' (len={len(emb_list) if isinstance(emb_list, list) else '?'}).")
                        continue
                    
                    # Convert to float32 numpy array
                    emb_np = np.array(emb_list, dtype="float32")
                    
                    known_faces.append({
                        "name": name,
                        "id": user_id,
                        "embedding": emb_np
                    })
                    print(f"[INFO] Loaded face for: {name}")

                except Exception as e:
                    print(f"[ERROR] Parsing embedding for '{name}' failed: {e}")

        except Exception as e:
            print(f"[ERROR] Network error during sync: {e}")
            # Depending on requirements, we might return empty list or retry
        
        return known_faces

    def send_data(self, data):
        """
        Sends screen data to Appwrite.
        """
        self.send_to_appwrite(data)

    def send_to_appwrite(self, data):
        """
        Sends activity data to the Appwrite Function.
        """
        # Hardcoded Function URL (Legacy support, maybe move to env later)
        APPWRITE_FUNCTION_URL = 'https://692d6ca4000b43d5b55e.fra.appwrite.run/'
        
        try:
            dt = datetime.fromisoformat(data['timestamp'])
            start_time = int(dt.timestamp())
            duration = int(data['duration'])
            end_time = start_time + duration
            day = dt.isoformat()
            
            payload = {
                "start_time": start_time,
                "duration": duration,
                "end_time": end_time,
                "day": day,
                "app_used": data['app']
            }
            
            response = requests.post(APPWRITE_FUNCTION_URL, json=payload)
            
            if response.status_code == 200:
                print(f"[Appwrite] Activity logged: {data['app']}")
            else:
                print(f"[Appwrite] Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[Appwrite] Failed to send data: {e}")

    def send_face_data(self, data):
        """
        Sends face data to Appwrite Face Receiver.
        """
        self.send_face_to_appwrite(data)

    def send_face_to_appwrite(self, data):
        """
        Sends face attendance data to the Appwrite Face Receiver Function.
        """
        APPWRITE_FACE_FUNCTION_URL = 'https://6930d3790014db9774a2.fra.appwrite.run/'
        
        name = data['name']
        user_id = data.get('user_id') # Expecting user_id to be passed now if possible

        if not user_id:
             # Fallback if logic doesn't pass ID yet (though refactor should fix this)
             pass 

        # We can pass the user_id directly if available, or just name if needed
        # But per new architecture, we should have IDs.
        # However, FaceLogger might just pass 'name' and 'confidence'.
        # Let's keep the logic simple: We send what we have.
        # If the tracking logic passes the ID, we use it.
        
        real_user_id = user_id if user_id else None
        
        # Legacy mapping fallback (can be removed if confident)
        USER_ID_MAPPING = {
            "vlad_face01": "6930cebb0023c5116a28"
        }
        if not real_user_id and name in USER_ID_MAPPING:
            real_user_id = USER_ID_MAPPING[name]
        
        if not real_user_id:
             # print(f"[Appwrite] No User ID for face: {name}")
             return

        try:
            dt = datetime.fromisoformat(data['timestamp'])
            start_time = int(dt.timestamp())
            end_time = start_time + 1
            day = dt.isoformat()

            payload = {
                "users": real_user_id,
                "start_time": start_time,
                "end_time": end_time,
                "day": day
            }
            
            response = requests.post(APPWRITE_FACE_FUNCTION_URL, json=payload)
            
            if response.status_code == 200:
                print(f"[Appwrite] Face attendance logged: {name} -> {real_user_id}")
            else:
                print(f"[Appwrite] Face Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[Appwrite] Failed to send face data: {e}")
