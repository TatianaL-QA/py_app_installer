import requests
from decouple import config
from pprint import pprint
from termcolor import *

while True:
    try:
        LIM = int(input("Limit the number of recent releases by: "))
        if LIM > 0:
            break  # Exit the loop if input is a positive integer
        else:
            print("Should be a positive integer greater than zero")
    except ValueError:
        print("Invalid input. Please enter a valid integer")


def print_debug(message):
    if config("DEBUG") == "True":
        print(message)


def get_release_ids(OWNER_NAME, APP_NAME, limit=LIM):
    print_debug("Calling get_release_ids")
    app_url = f"https://api.appcenter.ms/v0.1/apps/{OWNER_NAME}/{APP_NAME}/releases"
    api_token = config("APPCENTER_TOKEN")
    headers = {"X-API-Token": api_token}

    response = requests.get(app_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        release_ids = [release["id"] for release in data[:limit]
                       ] if limit else [release["id"] for release in data]
        print(f"{release_ids} total: {len(release_ids)}\n")
        return release_ids
    else:
        print(
            f"Failed to retrieve release IDs from AppCenter. Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        raise Exception("Failed to retrieve release IDs from AppCenter.")


def get_release_notes(OWNER_NAME, APP_NAME, release_ids):
    release_notes_dict = {}

    for release_id in release_ids:
        app_url = f"https://api.appcenter.ms/v0.1/apps/{OWNER_NAME}/{APP_NAME}/releases/{release_id}"
        api_token = config("APPCENTER_TOKEN")
        headers = {"X-API-Token": api_token}

        response = requests.get(app_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if "release_notes" in data:
                release_notes = data["release_notes"]
                if release_notes:
                    if isinstance(release_notes, str):
                        release_notes = [release_notes]
                    release_notes_dict[release_id] = release_notes
        else:
            print(f"Failed to retrieve release notes for release ID {release_id} from AppCenter. "
                  f"Status Code: {response.status_code}")
            print(f"Response Content: {response.content}")

    # pprint(release_notes_dict)
    return release_notes_dict


def search_releases_by_partial_notes(OWNER_NAME, APP_NAME, partial_notes):
    print_debug("Calling search_releases_by_partial_notes")
    matching_releases = {}

    release_ids = get_release_ids(OWNER_NAME, APP_NAME, limit=LIM)
    release_notes_dict = get_release_notes(OWNER_NAME, APP_NAME, release_ids)

    for release_id, release_notes in release_notes_dict.items():
        matching_notes = [
            note for note in release_notes if partial_notes.lower() in note.lower()]
        if matching_notes:
            matching_releases[release_id] = matching_notes
    return matching_releases


if __name__ == "__main__":
    OWNER_NAME = config("OWNER_NAME")
    APP_NAME = config("APP_NAME")
    partial_notes = str(
        input("Search for string (case insensitive): ")).lower()
    matching_releases = search_releases_by_partial_notes(
        OWNER_NAME, APP_NAME, partial_notes)

    for release_id, release_notes_list in matching_releases.items():
        print(colored(f"Release ID: {release_id}", "blue"))

        if isinstance(release_notes_list, list):
            for release_note in release_notes_list:
                print(colored(f"Release Notes:\n{release_note}", "cyan"))
        else:
            print(f"Release Note:\n{release_notes_list}")

        print("\n")
