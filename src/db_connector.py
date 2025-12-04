import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()



class DatabaseConnector:
    def __init__(self):
        print(f"[INFO] DatabaseConnector initialized (Appwrite only mode)")

    def _init_db(self):
        pass

    def send_data(self, data):
        """
        Sends screen data to Appwrite.
        """
        # Send to Appwrite
        self.send_to_appwrite(data)

    def send_to_appwrite(self, data):
        """
        Sends activity data to the Appwrite Function.
        """
        APPWRITE_FUNCTION_URL = 'https://692d6ca4000b43d5b55e.fra.appwrite.run/'
        
        try:
            # Convert ISO timestamp to Unix timestamp (seconds)
            dt = datetime.fromisoformat(data['timestamp'])
            start_time = int(dt.timestamp())
            duration = int(data['duration'])
            end_time = start_time + duration
            
            # Format day as ISO string (or just the date part if that's what Appwrite prefers, 
            # but 'datetime' type usually takes ISO)
            day = dt.isoformat()
            
            payload = {
                "start_time": start_time,
                "duration": duration,  # Required by Function validation
                "end_time": end_time,  # Required by DB schema
                "day": day,            # Required by DB schema
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
        # Send to Appwrite
        self.send_face_to_appwrite(data)

    def send_face_to_appwrite(self, data):
        """
        Sends face attendance data to the Appwrite Face Receiver Function.
        """
        APPWRITE_FACE_FUNCTION_URL = 'https://6930d3790014db9774a2.fra.appwrite.run/'
        
        # Mapping of face names to Appwrite User IDs
        USER_ID_MAPPING = {
            "vlad_face01": "6930cebb0023c5116a28"
        }
        
        name = data['name']
        if name not in USER_ID_MAPPING:
            # print(f"[Appwrite] No User ID mapping for face: {name}")
            return

        user_id = USER_ID_MAPPING[name]
        
        try:
            # Convert ISO timestamp to Unix timestamp (seconds)
            dt = datetime.fromisoformat(data['timestamp'])
            start_time = int(dt.timestamp())
            end_time = start_time + 1 # Momentary event
            day = dt.isoformat()

            payload = {
                "users": user_id,      # Changed from 'user_id' to 'users' to match DB column
                # "status": "present", # Removed 'status' as it's not in the schema
                "start_time": start_time,
                "end_time": end_time,
                "day": day
            }
            
            response = requests.post(APPWRITE_FACE_FUNCTION_URL, json=payload)
            
            if response.status_code == 200:
                print(f"[Appwrite] Face attendance logged: {name} -> {user_id}")
            else:
                print(f"[Appwrite] Face Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[Appwrite] Failed to send face data: {e}")
