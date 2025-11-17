import requests
from rclone_python import rclone
from datetime import datetime, timedelta
from aim.digifeeds.alma_client import AlmaClient
from aim.digifeeds.db_client import DBClient
from aim.services import S
from aim.hathifiles.client import Client as HathifilesClient
from requests.exceptions import HTTPError


class NotAddedToDigifeedsSetError(Exception):
    pass


class Item:
    """A Digifeeds Item

    An item to be processed by the Digifeeds process.

    Attributes:
        data: The item
    """

    def __init__(self, data: dict) -> None:
        """Initializes the instance with data argument.

        Args:
            data (dict): The item
        """
        self.data = data

    def has_status(self, status: str) -> bool:
        """The status of this Digifeeds Item.

        Args:
            status (str): A Digifeeds status.

        Returns:
            bool: True if Digifeeds item has a status, Fales if Digifeeds item does not have a status.
        """
        return any(s["name"] == status for s in self.data["statuses"])

    def add_to_digifeeds_set(self):
        if self.has_status("added_to_digifeeds_set"):
            return self

        try:
            AlmaClient().add_barcode_to_digifeeds_set(self.barcode)
        except HTTPError as ext_inst:
            errorList = ext_inst.response.json()["errorList"]["error"]
            if any(e["errorCode"] == "60120" for e in errorList):
                if not self.has_status("not_found_in_alma"):
                    item = Item(
                        DBClient().add_item_status(
                            barcode=self.barcode, status="not_found_in_alma"
                        )
                    )
                    return item
                else:
                    return self
            elif any(e["errorCode"] == "60115" for e in errorList):
                # 60115 means the barcode is already in the set. That means the
                # db entry from this barcdoe needs to have
                # added_to_digifeeds_set
                pass
            else:
                raise ext_inst
        item = Item(
            DBClient().add_item_status(
                barcode=self.barcode, status="added_to_digifeeds_set"
            )
        )
        return item

    def check_zephir(self):
        if self.has_status("in_zephir"):
            return self

        response = requests.get(f"{S.zephir_bib_api_url}/mdp.{self.barcode}")
        if response.status_code == 200:
            db_resp = DBClient().add_item_status(
                barcode=self.barcode, status="in_zephir"
            )
            return Item(db_resp)
        else:
            return None

    def move_to_pickup(self):
        if not self.in_zephir_for_long_enough:
            return None

        DBClient().add_item_status(barcode=self.barcode, status="copying_start")
        rclone.copyto(
            f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}/{self.barcode}.zip",
            f"{S.digifeeds_pickup_rclone_remote}:{self.barcode}.zip",
        )
        DBClient().add_item_status(barcode=self.barcode, status="copying_end")
        timestamp = datetime.now().strftime("%F_%H-%M-%S")
        rclone.moveto(
            f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}/{self.barcode}.zip",
            f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_processed_path}/{timestamp}_{self.barcode}.zip",
        )
        db_resp = DBClient().add_item_status(
            barcode=self.barcode, status="pending_deletion"
        )

        return Item(db_resp)

    def check_and_update_hathifiles_timestamp(self):
        if self.hathifiles_timestamp:
            S.logger.warn(
                "already_has_hathifiles_timestamp",
                message="item already has a hathifiles timestamp",
                barcode=self.barcode,
            )
            return

        hf_item = HathifilesClient().get_item(htid=f"mdp.{self.barcode}")

        if hf_item:
            db_resp = DBClient().update_hathifiles_timestamp(
                barcode=self.barcode,
                timestamp=datetime.fromisoformat(hf_item["rights_timestamp"]),
            )
            S.logger.info(
                "hathifiles_timestamp_updated",
                message="item was found in hathifiles; its timestamp has been updated",
                barcode=self.barcode,
            )
            return Item(db_resp)
        else:
            S.logger.info(
                "not_found_in_hathifiles",
                message="item was not found in the hathifiles database",
                barcode=self.barcode,
            )

    def add_status(self, barcode: str, status: str):
        db_resp = DBClient().add_item_status(barcode=barcode, status=status)
        return Item(db_resp)

    @property
    def barcode(self) -> str:
        """The barcode of the Digifeeds item.

        Returns:
            str: The barcode.
        """
        return self.data["barcode"]

    @property
    def hathifiles_timestamp(self) -> datetime | None:
        """The rights_timestamp from hathifiles of the Digifeeds item at the time of checking.

        Returns:
            datetime: The hathifiles timestamp.
        """
        if self.data["hathifiles_timestamp"]:
            return datetime.fromisoformat(self.data["hathifiles_timestamp"])

    @property
    def in_zephir_for_long_enough(self) -> bool:
        """
        Returns whether or not the item has had metadata in zephir for more than
        14 days. The production database saves timestamps in Eastern Time. K8s
        runs in UTC. Because this is checking days, this function doesn't set the
        timezone because it's not close enough to matter.

        Returns:
            bool: whether or not the item's metadata has been in zephir for more than 14 days.
        """
        waiting_period = 14  # days
        in_zephir_status = next(
            (
                status
                for status in self.data["statuses"]
                if status["name"] == "in_zephir"
            ),
            None,
        )
        if in_zephir_status is None:
            return False

        created_at = datetime.fromisoformat(in_zephir_status["created_at"])
        if created_at < (datetime.now() - timedelta(days=waiting_period)):
            return True
        else:
            return False


def get_item(barcode: str) -> Item | None:
    return Item(DBClient().get_or_add_item(barcode))


def process_item(item: Item) -> Item:
    barcode = item.barcode
    # if item.has_status("pending_deletion"):
    #     S.logger.info(
    #         "already_processed",
    #         message="item has already been moved so it does not need processing",
    #         barcode=barcode",
    #     )
    #     return None

    S.logger.info(
        "add_to_digifeeds_set_start",
        message="Start adding item to digifeeds set",
        barcode=barcode,
    )
    add_to_set_item = item.add_to_digifeeds_set()
    if add_to_set_item.has_status("not_found_in_alma"):
        S.logger.info(
            "not_found_in_alma", message="Item not found in alma.", barcode=barcode
        )

    if add_to_set_item.has_status("added_to_digifeeds_set"):
        S.logger.info(
            "added_to_digifeeds_set",
            message="Item added to digifeeds set",
            barcode=barcode,
        )
    else:
        S.logger.error(
            "not_added_to_digifeeds_set",
            message="Item NOT added to digifeeds set",
            barcode=barcode,
        )
        return add_to_set_item

    check_zephir_item = add_to_set_item.check_zephir()
    if check_zephir_item:
        S.logger.info("in_zephir", message="Item is in zephir", barcode=barcode)
    else:
        S.logger.info("not_in_zephir", message="Item is NOT in zephir", barcode=barcode)
        return check_zephir_item

    move_to_pickup_item = check_zephir_item.move_to_pickup()
    if move_to_pickup_item is None:
        S.logger.info(
            "not_in_zephir_long_enough",
            message="Item has not been in zephir long enough",
            barcode=barcode,
        )
    else:
        S.logger.info(
            "move_to_pickup_success",
            message="Item has been successfully moved to pickup",
            barcode=barcode,
        )
