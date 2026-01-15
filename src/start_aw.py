import subprocess
import time
import sys
import os

def start_process(command, name):
    print(f"[INFO] Starting {name}...")
    try:
        # Use Popen to start the process in the background
        # We redirect stdout/stderr to avoid cluttering the console, or we could log them
        proc = subprocess.Popen(command, shell=True)
        print(f"[INFO] {name} started with PID {proc.pid}")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start {name}: {e}")
        return None

def main():
    # Configuration is now handled via .env and Appwrite variables
    pass

    processes = []
    
    # 1. Start aw-server
    server_proc = start_process(f'"{sys.executable}" -m aw_server', "aw-server")
    if server_proc:
        processes.append(server_proc)
    
    # Wait a bit for server to start
    time.sleep(5)
    
    # 2. Start aw-watcher-window
    window_proc = start_process(f'"{sys.executable}" -m aw_watcher_window', "aw-watcher-window")
    if window_proc:
        processes.append(window_proc)

    # 3. Start screen_tracker.py
    # We run it as a module to handle relative imports
    tracker_proc = start_process(f'"{sys.executable}" -m src.screen_tracker', "screen_tracker")
    if tracker_proc:
        processes.append(tracker_proc)

    # 4. Start face_logger.py
    face_proc = start_process(f'"{sys.executable}" -m src.face_logger', "face_logger")
    if face_proc:
        processes.append(face_proc)

    print("[INFO] All processes started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for p in processes:
                if p.poll() is not None:
                    print(f"[WARN] Process {p.args} exited with code {p.returncode}")
                    # Optionally restart or exit
                    
    except KeyboardInterrupt:
        print("\n[INFO] Stopping processes...")
        for p in processes:
            p.terminate()
            # p.wait() # Wait for termination
        print("[INFO] Done.")

if __name__ == "__main__":
    main()
