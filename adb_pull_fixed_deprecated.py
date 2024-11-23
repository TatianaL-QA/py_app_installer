import subprocess
import os
from datetime import datetime, timedelta, timezone

FILEMASK = '*.mp4'
DEST = r"E:\dest"
TIME_DIFF = 1  # hours


def get_file_creation_time(device_id, file_info):
    creation_time_str, _ = file_info.split(' ', 1)
    creation_time = datetime.fromtimestamp(int(creation_time_str), tz=timezone.utc)
    return creation_time


def get_connected_devices():
    devices_command = "adb devices -l"
    devices_output = subprocess.check_output(
        devices_command, shell=True, text=True)
    devices_lines = devices_output.strip().split('\n')[1:]

    devices = []
    for line in devices_lines:
        fields = line.split()
        device_id = fields[0]
        device_name = fields[-1]
        devices.append({"id": device_id, "name": device_name})

    return devices


def select_device(devices):
    if len(devices) == 1:
        return devices[0]["id"]
    else:
        # print the list and prompt to select one
        print("List of connected devices:")
        for i, device in enumerate(devices, start=1):
            print(f"{i}. {device['id']}")

        while True:
            try:
                choice = int(
                    input("Provide the corresponding number: "))
                if 1 <= choice <= len(devices):
                    return devices[choice - 1]["id"]
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")


def pull_files_recent(device_id, local_destination_folder):
    # Formulate the adb command to list files and their creation times on the device
    list_command = f"adb -s {device_id} shell find /sdcard/ -type f -name {FILEMASK} -exec stat -c '%Y %n' {{}} +"

    # Execute the adb command and capture the output
    try:
        file_list_info = subprocess.check_output(
            list_command, shell=True, text=True).split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error listing files on the device: {e}")
        return

    # Remove empty strings from the list
    file_list_info = [file_info.strip()
                      for file_info in file_list_info if file_info.strip()]

    if not file_list_info:
        print("No files matching the pattern found on the device.")
        return

    # create local destination folder if doesn't exist
    os.makedirs(local_destination_folder, exist_ok=True)
    current_time = datetime.now(timezone.utc)

    # loop through list of files and pull files created within the last 24 hours
    for file_info in file_list_info:
        # Split the file_info into creation time and file path
        creation_time_str, file_path = file_info.split(' ', 1)

        # Convert the creation time to a datetime object with UTC timezone
        creation_time = datetime.fromtimestamp(int(creation_time_str), tz=timezone.utc)

        # Debug print: Show file creation time and current time
        print(f"Checking file '{file_path}':")
        print(f"  Creation time: {creation_time}")
        print(f"  Current time: {current_time}")
        print(f"  Time difference: {current_time - creation_time}")

        if current_time - creation_time < timedelta(hours=TIME_DIFF):
            local_pull_path = os.path.join(
                local_destination_folder, os.path.basename(file_path))
            pull_command = f'adb -s {device_id} pull "{file_path}" "{local_pull_path}"'
            print(f"Executing pull command: {pull_command}")

            result = subprocess.run(pull_command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"File '{os.path.basename(file_path)}' created on {creation_time} pulled to '{local_pull_path}'")
            else:
                print(f"Failed to pull file '{file_path}': {result.stderr}")


if __name__ == "__main__":

    devices = get_connected_devices()

    if not devices:
        print("No devices found. Make sure one or more Android devices were connected having proper Permissions")
    else:
        selected_device_id = select_device(devices)
        local_destination_folder = DEST

        pull_files_recent(selected_device_id, local_destination_folder)
