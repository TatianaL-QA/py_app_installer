import subprocess

ADB_PATH = "adb"


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
