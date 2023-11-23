import subprocess
import os
from datetime import datetime, timedelta


def get_file_creation_time(device_id, file_path):
    # Formulate the adb command to get the creation timestamp of the file
    stat_command = f"adb -s {device_id} shell stat -c %Y {file_path}"

    # Execute the adb command and capture the output
    creation_timestamp = int(subprocess.check_output(stat_command, shell=True, text=True).strip())

    # Convert the timestamp to a datetime object
    creation_time = datetime.utcfromtimestamp(creation_timestamp)

    return creation_time


def pull_files_recent(device_id, source_folder, local_destination_folder):
    # Formulate the adb command to list files matching the pattern on the device
    list_command = f"adb -s {device_id} shell ls -l {source_folder}/XR*.mp4"

    # Execute the adb command and capture the output
    file_list_info = subprocess.check_output(list_command, shell=True, text=True).split('\n')

    # Remove empty strings from the list
    file_list_info = [file_info.strip() for file_info in file_list_info if file_info.strip()]

    if not file_list_info:
        print("No files matching the pattern found on the device.")
        return

    # Create the local destination folder if it doesn't exist
    os.makedirs(local_destination_folder, exist_ok=True)

    # Get the current time
    current_time = datetime.utcnow()

    # Loop through the list of files and pull each file created within the last 24 hours
    for file_info in file_list_info:
        # Split the file info into fields
        fields = file_info.split()

        # Extract the file name from the last field
        file_name = fields[-1]

        # Extract the file path
        file_path = f"{source_folder}/{file_name}"

        # Get the file creation time
        creation_time = get_file_creation_time(device_id, file_path)

        # Check if the file was created within the last 24 hours
        if current_time - creation_time < timedelta(hours=24):
            local_pull_path = os.path.join(local_destination_folder, file_name)
            pull_command = f"adb -s {device_id} pull {file_path} {local_pull_path}"
            subprocess.run(pull_command, shell=True)
            print(f"File '{file_name}' pulled to '{local_pull_path}'")


if __name__ == "__main__":
    # Replace 'your_device_id' and 'your_source_folder' with your actual values
    device_id = "your_device_id"
    source_folder = "your_source_folder"

    # Replace 'C:\\Your\\Local\\Path' with your actual local path on the Windows machine
    local_destination_folder = "E:\\destination"

    pull_files_recent(device_id, source_folder, local_destination_folder)
