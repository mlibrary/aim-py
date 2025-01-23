import requests
import json
import os
from typing import Type
from aim.services import S


def filter_for_update_files(hathi_file_list: list) -> list:
    return [d["filename"] for d in hathi_file_list if not d["full"]]


def get_latest_update_files():
    return filter_for_update_files(get_hathi_file_list())


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


def create_store_file(store_path: str = S.hathifiles_store_path) -> None:
    if os.path.exists(store_path):
        S.logger.info("HathiFiles store file already exists. Leaving alone.")
    else:
        update_files_list = get_latest_update_files()
        with open(store_path, "w") as f:
            json.dump(update_files_list, f, ensure_ascii=False, indent=4)
        S.logger.info("Created Hathifiles store file")


class NewFileHandler:
    def __init__(self, new_files: list, store: list) -> None:
        self.new_files = new_files
        self.store = store

    def notify_webhook(self):
        response = requests.post(
            S.hathifiles_webhook_url, json={"file_names": self.new_files}
        )
        if response.status_code == 200:
            S.logger.info("Notify webhook SUCCESS")
        else:
            response.raise_for_status()

    def replace_store(self, store_path: str = S.hathifiles_store_path):
        with open(store_path, "w") as f:
            json.dump((self.store + self.new_files), f, ensure_ascii=False, indent=4)

        S.logger.info("Update store SUCCESS")


def check_for_new_update_files(
    latest_update_files: list | None = None,
    store: list | None = None,
    new_file_handler_klass: Type[NewFileHandler] = NewFileHandler,
):
    if latest_update_files is None:  # pragma: no cover
        latest_update_files = get_latest_update_files()

    if store is None:  # pragma: no cover
        store = get_store()

    new_files = [filename for filename in latest_update_files if filename not in store]

    if not new_files:
        S.logger.info("No new Hathifiles update files")
    else:
        S.logger.info("New Hathifiles update file(s)", file_names=",".join(new_files))

        handler = new_file_handler_klass(new_files=new_files, store=store)
        handler.notify_webhook()
        handler.replace_store()
