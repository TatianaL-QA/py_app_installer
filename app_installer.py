import os
import requests
import subprocess
from decouple import config
import argparse

ADB_PATH = "adb"


def check_internet_connection():
    try:
        requests.get("https://google.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False


def get_latest_download_url(app_identifier='mwl'):
    api_url_key = f"APPCENTER_{app_identifier.upper()}_URL"
    app_url = config(api_url_key)
    api_token = config("APPCENTER_TOKEN")

    headers = {"X-API-Token": api_token}
    response = requests.get(app_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        download_url = data["download_url"]
        package_name = data["bundle_identifier"]
        app_version = data["short_version"] + ' ' + data["version"]
        release_notes = data["release_notes"]
        return download_url, package_name, app_version, release_notes
    else:
        raise Exception("Failed to retrieve download URL from AppCenter.")


def download_and_store_app(app_identifier, download_url, output_folder):
    response = requests.get(download_url)
    if response.status_code == 200:
        apk_filename = os.path.join(output_folder, f"{app_identifier}.apk")
        with open(apk_filename, "wb") as apk_file:
            apk_file.write(response.content)
        return apk_filename
    else:
        raise Exception("Failed to download the app.")


def get_connected_adb_devices():
    devices = subprocess.check_output(
        [ADB_PATH, "devices"]).decode().split("\n")[1:-1]
    connected_devices = [device.split("\t")[0].strip() for device in devices if device.strip()]
    return connected_devices


def uninstall_app(bundle_identifier, device_id):
    adb_path = "adb"
    try:
        result = subprocess.run(
            [adb_path, "-s", device_id, "uninstall", bundle_identifier],
            capture_output=True,
            text=True,
            check=True
        )
        if "Success" in result.stdout:
            print(f"Successfully uninstalled on {device_id}")
        else:
            print(f"Package {bundle_identifier} not found on {device_id}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while uninstalling the app: {e}\n")


def install_app(apk_path, device_id):
    adb_path = "adb"
    subprocess.run([adb_path, "-s", device_id, "install", apk_path])


def get_app_info(package_name, app_version, release_notes):
    return (
        f"Downloaded package {package_name}, version {app_version}\n"
        f"Release notes: {release_notes}\n"
        "Success"
    )


def main():
    parser = argparse.ArgumentParser(description="Install app using AppCenter API.")
    parser.add_argument("--ml", action="store_true", help="Install ml instead of mwl")

    args = parser.parse_args()

    internet_connected = check_internet_connection()
    if not internet_connected:
        print("No internet connection.")
    else:
        if args.ml:
            app_identifier = 'ml'
        else:
            app_identifier = 'mwl'

        download_url, package_name, app_version, release_notes = get_latest_download_url(app_identifier)
        app_info = get_app_info(package_name, app_version, release_notes)
        print(f"{app_info}\n")
        output_folder = os.path.join(os.getcwd(), "downloads")
        os.makedirs(output_folder, exist_ok=True)

        apk_path = download_and_store_app(app_identifier, download_url, output_folder)
        connected_devices = get_connected_adb_devices()

        for device_id in connected_devices:
            uninstall_app(package_name, device_id)
            install_app(apk_path, device_id)
            print(f"App was installed on device '{device_id}'")


if __name__ == "__main__":
    main()
