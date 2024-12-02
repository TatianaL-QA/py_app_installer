import os
import requests
from adb_module import *
from decouple import config
import argparse


def check_internet_connection():
    try:
        requests.get("https://google.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False


# TODO: Add ability to grab a list of downloaded apps, select one from the list and install
#  after removing existing package
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
        app_version = data["short_version"] + '_' + data["version"]
        release_notes = data["release_notes"]
        return download_url, package_name, app_version, release_notes
    else:
        raise Exception("Failed to retrieve download URL from AppCenter.")


def download_and_store_app(
        app_identifier,
        download_url,
        output_folder,
        app_version):
    """Function is downloading the Android latest app using Appcenter API
     note: in case app is needed by bundle_number, other API endpoint should be used"""
    response = requests.get(download_url)
    if response.status_code == 200:
        apk_filename = os.path.join(
            output_folder, f"{app_identifier}_{app_version}.apk")
        with open(apk_filename, "wb") as apk_file:
            apk_file.write(response.content)
        return apk_filename
    else:
        raise Exception("Failed to download the app.")


def get_app_info(package_name, app_version, release_notes):
    return (
        f"Downloaded package {package_name}, version {app_version}\n"
        f"Release notes: {release_notes}\n"
        "Success"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Install app using AppCenter API.")
    parser.add_argument(
        "--ml",
        action="store_true",
        help="Use --ml to install ML! app, --mwl is default parameter")

    args = parser.parse_args()

    internet_connected = check_internet_connection()
    if not internet_connected:
        print("No internet connection.")
    else:
        if args.ml:
            app_identifier = 'ml'
        else:
            app_identifier = 'mwl'

        download_url, package_name, app_version, release_notes = get_latest_download_url(
            app_identifier)
        app_info = get_app_info(package_name, app_version, release_notes)
        print(f"{app_info}\n")
        output_folder = os.path.join(os.getcwd(), "downloads")
        os.makedirs(output_folder, exist_ok=True)

        apk_path = download_and_store_app(
            app_identifier, download_url, output_folder, app_version)
        connected_devices = get_connected_adb_devices()

        for device_id in connected_devices:
            uninstall_app(package_name, device_id)
            install_app(apk_path, device_id)
            print(f"App was installed on device '{device_id}'")


if __name__ == "__main__":
    main()
