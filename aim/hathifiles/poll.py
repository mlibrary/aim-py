import requests
import json
from aim.services import S


def filter_for_update_files(hathi_file_list: list) -> list:
    return [d["filename"] for d in hathi_file_list if not d["full"]]


def get_hathi_file_list() -> list:
    response = requests.get(
        "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    )
    if response.status_code != 200:
        response.raise_for_status()
    return response.json()


def get_store(store_path: str = S.hathifiles_store_path) -> list:
    with open(store_path) as f:
        file_list = json.load(f)
    return file_list
