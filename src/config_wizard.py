import os
import tkinter as tk
from tkinter import messagebox

ENV_FILE = ".env"

def create_env_file(db_string):
    try:
        with open(ENV_FILE, "w") as f:
            f.write(f"DB_CONNECTION_STRING={db_string}\n")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save config: {e}")
        return False

def on_submit(entry, root):
    db_string = entry.get().strip()
    if not db_string:
        db_string = "sqlite:///activity_data.db" # Default
    
    if create_env_file(db_string):
        messagebox.showinfo("Success", "Configuration saved! Starting application...")
        root.destroy()

def ensure_config():
    if os.path.exists(ENV_FILE):
        return

    root = tk.Tk()
    root.title("Panopticon Setup")
    root.geometry("400x200")

    label = tk.Label(root, text="Enter Database Connection String:\n(Leave empty for default SQLite)", pady=10)
    label.pack()

    entry = tk.Entry(root, width=50)
    entry.insert(0, "sqlite:///activity_data.db")
    entry.pack(pady=5)

    submit_btn = tk.Button(root, text="Save & Start", command=lambda: on_submit(entry, root))
    submit_btn.pack(pady=20)

    # Handle window close without saving
    def on_closing():
        if messagebox.askokcancel("Quit", "Configuration is required to start. Quit?"):
            root.destroy()
            exit(1)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    ensure_config()
