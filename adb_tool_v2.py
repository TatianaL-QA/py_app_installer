# adb_tool.py (Unified & Refactored ADB Tool)

import subprocess
import os
from datetime import datetime, timedelta, timezone
import logging
import argparse
from typing import List, Dict, Optional

# === Configuration ===
ADB_PATH = "adb"
DEFAULT_FILEMASK = "*.mp4"
DEFAULT_DEST = os.getenv("ADB_DEST", r"E:\\dest")
DEFAULT_TIME_DIFF = int(os.getenv("TIME_DIFF", "1"))

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# === ADB Utilities ===
def execute_adb_command(args: List[str], device_id: Optional[str] = None,
                        capture_output: bool = True) -> subprocess.CompletedProcess:
    cmd = [ADB_PATH]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(args)

    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        shell=False,
        check=False
    )


def get_connected_devices() -> List[Dict[str, str]]:
    result = execute_adb_command(["devices", "-l"])
    lines = result.stdout.strip().split('\n')[1:]

    devices = []
    for line in lines:
        if line.strip():
            parts = line.split()
            devices.append({"id": parts[0], "name": parts[-1] if len(parts) > 1 else "unknown"})
    return devices


def select_device(devices: List[Dict[str, str]]) -> str:
    if len(devices) == 1:
        return devices[0]["id"]

    logging.info("List of connected devices:")
    for idx, dev in enumerate(devices, 1):
        print(f"{idx}. {dev['id']} ({dev['name']})")

    while True:
        try:
            choice = int(input("Select device number: "))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]["id"]
        except ValueError:
            pass
        print("Invalid selection. Try again.")


# === App Management ===
def uninstall_app(bundle_identifier: str, device_id: str) -> bool:
    result = execute_adb_command(["uninstall", bundle_identifier], device_id)
    if "Success" in result.stdout:
        logging.info(f"Uninstalled {bundle_identifier} from {device_id}")
        return True
    else:
        logging.warning(f"Failed to uninstall {bundle_identifier}: {result.stdout.strip()}")
        return False


def install_app(apk_path: str, device_id: str) -> bool:
    result = execute_adb_command(["install", apk_path], device_id)
    if result.returncode == 0:
        logging.info(f"Installed {apk_path} on {device_id}")
        return True
    else:
        logging.error(f"Install failed: {result.stderr.strip()}")
        return False


# === File Operations ===
def pull_recent_files(device_id: str, dest_folder: str, filemask: str = DEFAULT_FILEMASK,
                      time_diff_hours: int = DEFAULT_TIME_DIFF):
    list_cmd = f"find /sdcard/ -type f -name '{filemask}' -exec stat -c '%Y %n' {{}} +"
    result = execute_adb_command(["shell", list_cmd], device_id)

    if result.returncode != 0:
        logging.error(f"File listing failed: {result.stderr.strip()}")
        return

    files_info = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    if not files_info:
        logging.info("No matching files found.")
        return

    os.makedirs(dest_folder, exist_ok=True)
    now = datetime.now(timezone.utc)

    for line in files_info:
        try:
            ts_str, path = line.split(' ', 1)
            ctime = datetime.fromtimestamp(int(ts_str), tz=timezone.utc)

            if now - ctime < timedelta(hours=time_diff_hours):
                filename = os.path.basename(path)
                local_path = os.path.join(dest_folder, filename)
                result = execute_adb_command(["pull", path, local_path], device_id)

                if result.returncode == 0:
                    logging.info(f"Pulled {filename} to {local_path}")
                else:
                    logging.warning(f"Failed to pull {path}: {result.stderr.strip()}")
        except Exception as e:
            logging.error(f"Failed to parse file info line '{line}': {e}")


# Pull recent .mp4 files from a device
# py adb_tool_v2.py --pull-recent
# Install an APK
# py adb_tool_v2.py --install path/to/app.apk
# Uninstall an app
# py adb_tool_v2.py --uninstall com.example.app
# Pull only .jpg files from last 2 hours to a custom folder
# py adb_tool_v2.py --pull-recent --mask "*.jpg" --hours 2 --dest "D:/media"


# === New Capture Utilities ===
import re
import sys
import threading
import msvcrt  # works on Windows for key press


def sanitize_jira_task(jira_input: str) -> str:
    """Extract Jira key like ABC-1234 from either plain text or URL."""
    match = re.search(r"[A-Z]{2,}-\d+", jira_input)
    return match.group(0) if match else jira_input


def build_filename(capture_type: str, jira_task: str, platf: str, env: str, mode: str) -> str:
    """Construct filename based on type, task, platform, env, timestamp, and mode."""
    jira_task = sanitize_jira_task(jira_task)
    prefix = "verified_" if capture_type == "v" else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    ext = "mp4" if mode == "rec" else "png"

    return f"{prefix}{jira_task}_{platf}_{env}_{timestamp}.{ext}"


def take_screenshot(device_id: str, local_dest: str, filename: str):
    """
    Take a screenshot, pull it locally, and clean up remote file.
    Always handles errors gracefully.
    """
    remote_path = f"/sdcard/{filename}"
    print("📸 Taking screenshot...")

    try:
        # Take screenshot on device
        result = execute_adb_command(["shell", "screencap", "-p", remote_path], device_id)
        if result.returncode != 0:
            logging.error(f"Failed to take screenshot: {result.stderr.strip()}")
            return

        # Ensure destination exists
        os.makedirs(local_dest, exist_ok=True)
        local_path = os.path.join(local_dest, filename)

        # Pull screenshot
        result = execute_adb_command(["pull", remote_path, local_path], device_id)
        if result.returncode != 0:
            logging.error(f"Failed to pull screenshot: {result.stderr.strip()}")
            return

        print(f"✅ Saved: {local_path}")

    finally:
        # Cleanup: remove remote file, even if pull failed
        execute_adb_command(["shell", "rm", "-f", remote_path], device_id)


def wait_for_space(stop_event):
    """Wait for SPACE key across platforms, set stop_event when pressed."""
    if os.name == "nt":
        import msvcrt
        while not stop_event.is_set():
            if msvcrt.kbhit() and msvcrt.getch() == b" ":
                stop_event.set()
                break
    else:
        import termios, tty, select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not stop_event.is_set():
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    ch = sys.stdin.read(1)
                    if ch == " ":
                        stop_event.set()
                        break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def record_screen(device_id: str, local_dest: str, filename: str):
    """
    Start screen recording. Stop with SPACE (preferred) or Ctrl+C (fallback).
    Always pulls and deletes the remote file afterwards.
    """
    remote_path = f"/sdcard/{filename}"
    print("🎥 Recording started... Press SPACE or Ctrl+C to stop")

    process = subprocess.Popen(
        [ADB_PATH, "-s", device_id, "shell", "screenrecord", remote_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    stop_event = threading.Event()
    listener = threading.Thread(target=wait_for_space, args=(stop_event,), daemon=True)
    listener.start()

    try:
        while not stop_event.is_set():
            process.poll()
            if process.returncode is not None:
                break
            threading.Event().wait(0.1)
    except KeyboardInterrupt:
        print("\n⏹️ Ctrl+C detected, stopping recording...")
        stop_event.set()

    if process.poll() is None:
        process.terminate()
    process.wait()

    # Pull and clean up
    os.makedirs(local_dest, exist_ok=True)
    local_path = os.path.join(local_dest, filename)
    execute_adb_command(["pull", remote_path, local_path], device_id)
    execute_adb_command(["shell", "rm", remote_path], device_id)
    print(f"✅ Saved: {local_path}")


def android_capture(device_id: str, capture_type: str, mode: str, jira_task: str, platf: str, env: str,
                    dest_folder: str):
    # platf = "AND" #add later: logic to identify capture mechanism (adb or xcode), when iOS capture is added

    filename = build_filename(capture_type, jira_task, platf, env, mode)
    if mode == "scr":
        take_screenshot(device_id, dest_folder, filename)
    elif mode == "rec":
        record_screen(device_id, dest_folder, filename)
    else:
        logging.error("Invalid mode. Use 'scr' for screenshot or 'rec' for recording.")


# === CLI Interface ===
def main():
    parser = argparse.ArgumentParser(description="ADB Utility Tool")
    parser.add_argument("--uninstall", help="Uninstall app by bundle identifier")
    parser.add_argument("--install", help="Install APK file path")
    parser.add_argument("--pull-recent", action="store_true", help="Pull recent media files")
    parser.add_argument("--mask", default=DEFAULT_FILEMASK, help="Filemask for pulling files")
    parser.add_argument("--dest", default=DEFAULT_DEST, help="Destination directory for pulled files")
    parser.add_argument("--hours", type=int, default=DEFAULT_TIME_DIFF, help="How recent (in hours) to pull files")

    parser.add_argument("--capture", action="store_true", help="Capture screenshot or recording")
    parser.add_argument("--type", choices=["v", "n"], help="Prefix type: v=verified, n=normal")
    parser.add_argument("--mode", choices=["scr", "rec"], help="Capture mode: scr=screenshot, rec=recording")
    parser.add_argument("--t", dest="task", help="Jira task ID or URL")
    parser.add_argument("--platf", required=False, default="AND")
    parser.add_argument("--env", required=False, default="DEV", help="Environment string")

    args = parser.parse_args()

    devices = get_connected_devices()
    if not devices:
        logging.error("No devices connected.")
        return

    device_id = select_device(devices)

    if args.uninstall:
        uninstall_app(args.uninstall, device_id)
    if args.install:
        install_app(args.install, device_id)
    if args.pull_recent:
        pull_recent_files(device_id, args.dest, args.mask, args.hours)

    if args.capture:
        if not args.type or not args.mode or not args.task:
            logging.error("Missing required args: --type, --mode, --t")
            return
        android_capture(device_id, args.type, args.mode, args.task, args.platf, args.env, args.dest)


if __name__ == "__main__":
    main()
