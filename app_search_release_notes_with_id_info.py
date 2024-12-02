import requests
from decouple import config
from termcolor import colored


def make_api_request(endpoint):
    api_token = config("APPCENTER_TOKEN")
    headers = {"X-API-Token": api_token}
    response = requests.get(endpoint, headers=headers)
    return response


def get_release_ids(OWNER_NAME, APP_NAME, limit):
    print_debug("Calling get_release_ids")
    endpoint = f"{config('API_BASE_URL')}/{OWNER_NAME}/{APP_NAME}/releases"
    response = make_api_request(endpoint)

    if response.status_code == 200:
        data = response.json()
        releases = data[:limit] if limit else data
        release_ids = [release["id"] for release in releases]
        print(f"{release_ids} total: {len(release_ids)}\n")
        return release_ids
    else:
        print(
            f"Failed to retrieve release IDs from AppCenter. Status Code: {
            response.status_code}")
        print(f"Response Content: {response.content}")
        raise Exception("Failed to retrieve release IDs from AppCenter.")


def get_release_notes(OWNER_NAME, APP_NAME, release_ids):
    release_notes_dict = {}

    for release_id in release_ids:
        endpoint = f"{
        config('API_BASE_URL')}/{OWNER_NAME}/{APP_NAME}/releases/{release_id}"
        response = make_api_request(endpoint)
        if response.status_code == 200:
            data = response.json()
            if "release_notes" in data:
                release_notes = data["release_notes"]
                if release_notes:
                    if isinstance(release_notes, str):
                        release_notes = [release_notes]
                    release_notes_dict[release_id] = {
                        "release_notes": release_notes,
                        "short_version": data.get("short_version"),
                        "version": data.get("version"),
                        "size": data.get("size")
                    }
        else:
            print(f"Failed to retrieve release notes for release ID {release_id} from AppCenter. "
                  f"Status Code: {response.status_code}")
            print(f"Response Content: {response.content}")

    return release_notes_dict


def search_releases_by_partial_notes(
        OWNER_NAME, APP_NAME, partial_notes, limit):
    release_ids = get_release_ids(OWNER_NAME, APP_NAME, limit=limit)
    release_notes_dict = get_release_notes(OWNER_NAME, APP_NAME, release_ids)

    matching_releases = {}

    for release_id, release_info in release_notes_dict.items():
        release_notes = release_info["release_notes"]
        matching_notes = [
            note for note in release_notes if partial_notes.lower() in note.lower()]
        if matching_notes:
            matching_releases[release_id] = {
                "release_notes": matching_notes,
                "short_version": release_info.get("short_version"),
                "version": release_info.get("version"),
                "size": release_info.get("size")
            }

    return matching_releases


def print_debug(message):
    if config("DEBUG") == "True":
        print(message)


if __name__ == "__main__":
    OWNER_NAME = config("OWNER_NAME")
    APP_NAME = config("APP_NAME")
    limit = int(input("Limit the number of recent releases by: "))
    partial_notes = str(
        input("Search for string (case insensitive): ")).lower()

    while limit <= 0:
        print("Should be a positive integer greater than zero")
        limit = int(input("Limit the number of recent releases by: "))

    matching_releases = search_releases_by_partial_notes(
        OWNER_NAME, APP_NAME, partial_notes, limit)

    for release_id, release_info in matching_releases.items():
        print(colored(f"Release ID: {release_id}", "blue"))
        print(
            colored(
                f"Version: {
                release_info.get('short_version')} ({
                release_info.get('version')})",
                "yellow"))
        print(colored(f"Size: {release_info.get('size')}", "cyan"))

        if isinstance(release_info["release_notes"], list):
            for release_note in release_info["release_notes"]:
                print(colored(f"Release Notes:\n{release_note}", "cyan"))

            print("\n")
        else:
            print(f"Release Note:\n{release_info['release_notes']}\n")
