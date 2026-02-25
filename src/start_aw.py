import subprocess
import time
import sys
import os

def start_process(command, name):
    """Start a subprocess and return (proc, name) tuple."""
    print(f"[INFO] Starting {name}...")
    try:
        proc = subprocess.Popen(
            command, 
            shell=True,
            stdout=sys.stdout,  # Pipe output to console so we can see errors
            stderr=sys.stderr
        )
        print(f"[INFO] {name} started with PID {proc.pid}")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start {name}: {e}")
        return None

def main():
    print("=" * 60)
    print("[INFO] PANOPTICON STARTUP")
    print(f"[INFO] Python: {sys.executable}")
    print(f"[INFO] DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    print("=" * 60)

    # Define all processes to run
    # Format: (command, name, required)
    process_defs = [
        (f'"{sys.executable}" -m aw_server', "aw-server", False),
        # aw-watcher-window SKIPPED — native X11 tracking is in screen_tracker 
        (f'"{sys.executable}" -m src.screen_tracker', "screen_tracker", True),
        (f'"{sys.executable}" -m src.face_logger', "face_logger", False),
        (f'"{sys.executable}" -m src.clock', "lcd_clock", False),
    ]

    # Start aw-server first and wait for it
    server_cmd, server_name, _ = process_defs[0]
    server_proc = start_process(server_cmd, server_name)
    
    print("[INFO] Waiting 5s for aw-server to initialize...")
    time.sleep(5)

    # Track running processes: list of (proc, command, name)
    running = []
    if server_proc:
        running.append((server_proc, server_cmd, server_name))

    # Start remaining processes
    for cmd, name, required in process_defs[1:]:
        proc = start_process(cmd, name)
        if proc:
            running.append((proc, cmd, name))
        elif required:
            print(f"[ERROR] Required process {name} failed to start!")

    print("[INFO] All processes started. Press Ctrl+C to stop.")
    print("[INFO] Monitoring processes for crashes...")

    try:
        while True:
            time.sleep(3)
            
            for i, (proc, cmd, name) in enumerate(running):
                if proc.poll() is not None:
                    exit_code = proc.returncode
                    print(f"[WARN] {name} exited with code {exit_code}. Restarting in 5s...")
                    time.sleep(5)
                    
                    new_proc = start_process(cmd, name)
                    if new_proc:
                        running[i] = (new_proc, cmd, name)
                    else:
                        print(f"[ERROR] Failed to restart {name}")

    except KeyboardInterrupt:
        print("\n[INFO] Stopping all processes...")
        for proc, _, name in running:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"[INFO] {name} stopped.")
            except Exception:
                proc.kill()
                print(f"[WARN] {name} killed.")
        print("[INFO] Done.")

if __name__ == "__main__":
    main()
