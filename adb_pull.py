import subprocess
import os
from datetime import datetime, timedelta


def get_file_creation_time(device_id, file_path):
    # Formulate the adb command to get the creation timestamp of the file
    stat_command = f"adb -s {device_id} shell stat -c %Y {file_path}"

    # Execute the adb command and capture the output
    try:
        creation_timestamp = int(subprocess.check_output(
            stat_command, shell=True, text=True).strip())
    except subprocess.CalledProcessError as e:
        print(f"Error getting file creation time: {e}")
        return None

    # Convert the timestamp to a datetime object
    creation_time = datetime.utcfromtimestamp(creation_timestamp)

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
        print("Select a device from the list:")
        for i, device in enumerate(devices, start=1):
            print(f"{i}. {device['name']}")

        while True:
            try:
                choice = int(
                    input("Enter the number corresponding to your choice: "))
                if 1 <= choice <= len(devices):
                    return devices[choice - 1]["id"]
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")


def pull_files_recent(device_id, local_destination_folder):
    # Formulate the adb command to list files matching the pattern on the device
    list_command = f"adb -s {device_id} shell find /sdcard/ -type f -name 'XR*.mp4'"

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

    # Initialize variables to track the most recently created file
    most_recent_file = None
    most_recent_creation_time = None

    # Loop through the list of files and find the most recently created file within the last 24 hours
    for file_info in file_list_info:
        # Extract the file name from the file path
        file_name = os.path.basename(file_info)

        # Get the file creation time
        creation_time = get_file_creation_time(device_id, file_info)

        if creation_time is not None:
            # Check if the file was created within the last 24 hours
            if current_time - creation_time < timedelta(hours=24):
                # Update the most_recent_file if it's the first iteration or if this file is more recent
                if most_recent_creation_time is None or creation_time > most_recent_creation_time:
                    most_recent_file = file_info
                    most_recent_creation_time = creation_time

    # Pull the most recently created file, if found

    if most_recent_file is not None:
        most_recent_file_name = os.path.basename(most_recent_file)
        local_pull_path = os.path.join(
            local_destination_folder, most_recent_file_name)
        # Quote the file paths to handle spaces in file names
        pull_command = f'adb -s {device_id} pull "{most_recent_file}" "{local_pull_path}"'
        subprocess.run(pull_command, shell=True)
        print(
            f"Most recently created file '{most_recent_file_name}' pulled to '{local_pull_path}'")
    else:
        print("No files matching the pattern found within the last 24 hours on the device.")


if __name__ == "__main__":
    # Get the list of connected devices
    devices = get_connected_devices()

    if not devices:
        print("No devices found. Make sure your Android device is connected.")
    else:
        # Select a device
        selected_device_id = select_device(devices)

        # Replace 'C:\\Your\\Local\\Path' with your actual local path on the Windows machine
        # ToDO: add proper folder checker, and propose either to select folder, or create a new one
        local_destination_folder = "e:\dest"

        pull_files_recent(selected_device_id, local_destination_folder)
