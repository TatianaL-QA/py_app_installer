import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import logging
import os

import android_capture
import ios_capture  # stub file, same API as android_capture for now

# === Configuration ===
DEST_FOLDER = os.getenv("CAPTURE_DEST", r"E:\captures")  # Windows default
os.makedirs(DEST_FOLDER, exist_ok=True)


# === Logging Handler for GUI ===
class TkinterLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.configure(state="disabled")
        self.text_widget.yview(tk.END)


# === GUI Application ===
class CaptureApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Capture Tool")
        self.geometry("720x600")

        self.stop_event = threading.Event()

        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        # --- Capture mode ---
        mode_frame = tk.LabelFrame(self, text="Capture mode", padx=5, pady=5)
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.capture_mode = tk.StringVar(value="rec")
        tk.Radiobutton(mode_frame, text="Recording", variable=self.capture_mode, value="rec").pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Screenshot", variable=self.capture_mode, value="scr").pack(side="left",
                                                                                                    padx=10)

        # --- Jira ticket ---
        jira_frame = tk.LabelFrame(self, text="Jira ticket", padx=5, pady=5)
        jira_frame.pack(fill="x", padx=10, pady=5)

        self.jira_entry = tk.Entry(jira_frame, width=80)
        self.jira_entry.pack(side="left", fill="x", expand=True)

        # --- Notation ---
        notation_frame = tk.LabelFrame(self, text="Notation", padx=5, pady=5)
        notation_frame.pack(fill="x", padx=10, pady=5)

        self.capture_type = tk.StringVar(value="n")
        tk.Radiobutton(notation_frame, text="Verified", variable=self.capture_type, value="v").pack(side="left",
                                                                                                    padx=10)
        tk.Radiobutton(notation_frame, text="Repro", variable=self.capture_type, value="r").pack(side="left", padx=10)
        tk.Radiobutton(notation_frame, text="None", variable=self.capture_type, value="n").pack(side="left", padx=10)

        # --- Platform ---
        platform_frame = tk.LabelFrame(self, text="Platform", padx=5, pady=5)
        platform_frame.pack(fill="x", padx=10, pady=5)

        self.platform = tk.StringVar(value="AND")
        tk.Radiobutton(platform_frame, text="Android", variable=self.platform, value="AND").pack(side="left", padx=10)
        tk.Radiobutton(platform_frame, text="iOS", variable=self.platform, value="iOS").pack(side="left", padx=10)

        # --- BFF / CAS ---
        bc_frame = tk.LabelFrame(self, text="BFF / CAS", padx=5, pady=5)
        bc_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(bc_frame, text="BFF").pack(side="left")
        self.bff_entry = tk.Entry(bc_frame, width=24)
        self.bff_entry.pack(side="left", padx=5)

        tk.Label(bc_frame, text="CAS").pack(side="left")
        self.cas_entry = tk.Entry(bc_frame, width=24)
        self.cas_entry.pack(side="left", padx=5)

        # --- Buttons ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(btn_frame, text="Start", command=self.start_capture).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Stop", command=self.stop_capture).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Reset", command=self.reset_fields).pack(side="left", padx=10)

        # --- Log output ---
        log_frame = tk.LabelFrame(self, text="Log Output", padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled", wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)

    def _setup_logging(self):
        handler = TkinterLogHandler(self.log_text)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    # === Button Actions ===
    def start_capture(self):
        capture_mode = self.capture_mode.get()
        capture_type = self.capture_type.get()
        jira = self.jira_entry.get().strip()
        platform = self.platform.get()
        bff = self.bff_entry.get().strip()
        cas = self.cas_entry.get().strip()

        self.stop_event.clear()

        def run_capture():
            try:
                if platform == "AND":
                    device_id = android_capture.get_default_device()
                    android_capture.android_capture(
                        device_id=device_id,
                        capture_type=capture_type,
                        mode=capture_mode,
                        jira_task=jira,
                        platf=platform,
                        dest_folder=DEST_FOLDER,
                        bff=bff,
                        cas=cas,
                        stop_event=self.stop_event,
                    )
                elif platform == "iOS":
                    ios_capture.ios_capture(
                        capture_type=capture_type,
                        mode=capture_mode,
                        jira_task=jira,
                        platf=platform,
                        dest_folder=DEST_FOLDER,
                        bff=bff,
                        cas=cas,
                        stop_event=self.stop_event,
                    )
                messagebox.showinfo("Capture Finished", "Capture saved successfully!")
            except Exception as e:
                logging.error(f"Capture failed: {e}")

        threading.Thread(target=run_capture, daemon=True).start()

    def stop_capture(self):
        self.stop_event.set()
        logging.info("⏹️ Stop signal sent.")

    def reset_fields(self):
        self.jira_entry.delete(0, tk.END)
        self.capture_type.set("n")
        self.capture_mode.set("rec")
        self.platform.set("AND")
        self.bff_entry.delete(0, tk.END)
        self.cas_entry.delete(0, tk.END)
        logging.info("Form reset.")

    def on_close(self):
        self.stop_event.set()
        self.destroy()


# === Run GUI ===
if __name__ == "__main__":
    app = CaptureApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
