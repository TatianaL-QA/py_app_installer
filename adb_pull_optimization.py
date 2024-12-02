import subprocess
import os
from datetime import datetime, timedelta
from decouple import config


def get_file_creation_time(device_id, file_info):
    # Split the file_info into creation time and file path
    creation_time_str, _ = file_info.split(' ', 1)

    # Convert the creation time to a datetime object
    creation_time = datetime.utcfromtimestamp(int(creation_time_str))

    return creation_time


def get_connected_devices():
    # Formulate the adb command to list connected devices
    devices_command = "adb devices -l"

    # Execute the adb command and capture the output
    devices_output = subprocess.check_output(
        devices_command, shell=True, text=True)

    # Split the output into lines and skip the first line (header)
    devices_lines = devices_output.strip().split('\n')[1:]

    # Extract device IDs and names
    devices = []
    for line in devices_lines:
        fields = line.split()
        device_id = fields[0]
        device_name = fields[-1]
        devices.append({"id": device_id, "name": device_name})

    return devices


def select_device(devices):
    if len(devices) == 1:
        # If only one device is available, use it by default
        return devices[0]["id"]
    else:
        # Print the list of available devices and prompt the user to select one
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
    # Formulate the adb command to list files and their creation times on the
    # device
    list_command = f"adb -s {device_id} shell find /sdcard/ -type f -name '*.jpg' -exec stat -c '%Y %n' {{}} +"

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

    # Create the local destination folder if it doesn't exist
    os.makedirs(local_destination_folder, exist_ok=True)

    # Get the current time
    current_time = datetime.utcnow()

    # Loop through the list of files and pull files created within the last 24
    # hours
    for file_info in file_list_info:
        # Split the file_info into creation time and file path
        creation_time_str, file_path = file_info.split(' ', 1)

        # Convert the creation time to a datetime object
        creation_time = datetime.utcfromtimestamp(int(creation_time_str))

        # Check if the file was created within the last 24 hours
        if current_time - creation_time < timedelta(hours=24):
            # Quote the file paths to handle spaces in file names
            local_pull_path = os.path.join(
                local_destination_folder, os.path.basename(file_path))
            pull_command = f'adb -s {device_id} pull "{file_path}" "{local_pull_path}"'
            subprocess.run(pull_command, shell=True)
            print(
                f"File '{
                os.path.basename(file_path)}' pulled to '{local_pull_path}'")


if __name__ == "__main__":
    # Get the list of connected devices
    devices = get_connected_devices()

    if not devices:
        print("No devices found. Make sure one or more Android devices were connected having proper Permissions")
    else:
        selected_device_id = select_device(devices)
        local_destination_folder = config("DESTINATION_LOCAL")

        pull_files_recent(selected_device_id, local_destination_folder)
