import subprocess
import logging
from datetime import datetime
import time
import os
import signal


def get_default_device() -> str:
    """Return the first connected Android device via adb, or raise an error."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()[1:]  # skip header
        devices = [line.split()[0] for line in lines if "device" in line]
        if not devices:
            raise RuntimeError("No Android devices connected.")
        return devices[0]
    except Exception as e:
        raise RuntimeError(f"Failed to get default device: {e}")


def build_filename(capture_type: str, jira_task: str, platf: str, bff: str, cas: str, mode: str) -> str:
    """Builds a standardized filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    ext = "mp4" if mode == "rec" else "png"

    parts = []
    if capture_type == "v":
        parts.append("verified")
    elif capture_type == "r":
        parts.append("repro")

    if jira_task:
        parts.append(jira_task)

    parts.append(platf)

    if bff:
        parts.append(bff)
    if cas:
        parts.append(cas)

    parts.append(timestamp)

    return "_".join(parts) + f".{ext}"


def android_capture(device_id: str, capture_type: str, mode: str,
                    jira_task: str, platf: str, dest_folder: str,
                    bff: str = "", cas: str = "", stop_event=None):
    """Handles Android screen recording or screenshot."""
    filename = build_filename(capture_type, jira_task, platf, bff, cas, mode)
    dest_path = os.path.join(dest_folder, filename)

    if mode == "scr":
        logging.info("📸 Taking screenshot...")
        subprocess.run(["adb", "-s", device_id, "exec-out", "screencap", "-p"], stdout=open(dest_path, "wb"))
        logging.info(f"✅ Screenshot saved: {dest_path}")
        return

    if mode == "rec":
        logging.info("🎥 Recording started... Press STOP in GUI to finish.")

        try:
            # Clean up any stale recording file from previous runs
            subprocess.run(["adb", "-s", device_id, "shell", "rm", "-f", "/sdcard/tmp_record.mp4"])

            proc = subprocess.Popen(
                ["adb", "-s", device_id, "shell", "screenrecord", "/sdcard/tmp_record.mp4"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )

            if stop_event:
                stop_event.wait()
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    proc.send_signal(signal.SIGINT)

            # Wait until adb has fully stopped and flushed the file
            proc.wait()

            # Extra safety: small delay to ensure file headers are written
            time.sleep(2)

            subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/tmp_record.mp4", dest_path])
            subprocess.run(["adb", "-s", device_id, "shell", "rm", "/sdcard/tmp_record.mp4"])
            logging.info(f"✅ Recording saved: {dest_path}")
        except Exception as e:
            logging.error(f"Recording failed: {e}")
