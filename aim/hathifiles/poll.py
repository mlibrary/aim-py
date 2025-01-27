import requests
import json
import os
from datetime import datetime, timedelta
from typing import Type
from aim.services import S


def filter_for_update_files(hathi_file_list: list) -> list:
    """
    Takes a plain hathifile_file_list list and filters to get only the file
    names for update files

    Args:
        hathi_file_list (list): full list of current hathifiles from hathitrust.org

    Returns:
        list: flat list of update file names
    """
    return [d["filename"] for d in hathi_file_list if not d["full"]]


def get_latest_update_files():
    """
    Gets the latest list of current hathifiles from hathitrust.org and filters
    for just a list of update files.

    Returns:
        list: flat list of update file names
    """
    return filter_for_update_files(get_hathi_file_list())


def get_hathi_file_list() -> list:
    """
    Gets the latest current list of hathifiles from hathitrust.org.

    Returns:
        list: list of dictionairies that describe hathifiles
    """
    response = requests.get(
        "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    )
    if response.status_code != 200:
        response.raise_for_status()
    return response.json()


def get_store(store_path: str = S.hathifiles_store_path) -> list:
    """
    Loads the store file that contains the list of all hathifile update files
    that have been seen before.

    Args:
        store_path (str, optional): path to the store file. Defaults to S.hathifiles_store_path.

    Returns:
        list: list of hathifile update files that have been seen before
    """
    with open(store_path) as f:
        file_list = json.load(f)
    return file_list


def create_store_file(store_path: str = S.hathifiles_store_path) -> None:
    """
    Creates a store file of the current list of update files from hathitrust.org
    if there does not already exist a store file.

    Args:
        store_path (str, optional): path to store file. Defaults to S.hathifiles_store_path.
    """

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
        """
        Sends a list of update files that haven't been seen to the argo events
        webhook for hathifiles.
        """
        response = requests.post(
            S.hathifiles_webhook_url, json={"file_names": self.new_files}
        )
        if response.status_code == 200:
            S.logger.info("Notify webhook SUCCESS")
        else:
            response.raise_for_status()

    @property
    def slim_store(self):
        """
        Removes files from the store that are over one year old

        Returns:
            list: list of update files that are newer than one year
        """
        last_year = datetime.today() - timedelta(days=365)
        slimmed_store = []
        for file_name in self.store:
            end = file_name.split("_")[2]
            date = datetime.strptime(end.split(".")[0], "%Y%m%d")
            if date > last_year:
                slimmed_store.append(file_name)
        return slimmed_store

    def replace_store(self, store_path: str = S.hathifiles_store_path):
        """
        Replaces the store file with a list of hathifile update files

        Args:
            store_path (str, optional):  path to hathifiles store file. Defaults to S.hathifiles_store_path.
        """
        with open(store_path, "w") as f:
            json.dump(
                (self.slim_store + self.new_files), f, ensure_ascii=False, indent=4
            )

        S.logger.info("Update store SUCCESS")


def check_for_new_update_files(
    latest_update_files: list | None = None,
    store: list | None = None,
    new_file_handler_klass: Type[NewFileHandler] = NewFileHandler,
):
    """
    Gets the latest list of hathifiles from hathitrust.org, loads up the store
    file and compares them. If there are new files triggers the argo events
    webhook and updates the store. If there are no new files, it exits.

    Args:
        latest_update_files (list | None, optional): list of latest update files. This will call get_latest_update_files() when None is given.
        store (list | None, optional): list of hathifiles update files that have been seen before. This will call get_store() if None is given.
        new_file_handler_klass (Type[NewFileHandler], optional): Class that handles new update files. Defaults to NewFileHandler.
    """
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
