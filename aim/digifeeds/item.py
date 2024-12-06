from datetime import datetime, timedelta
from aim.digifeeds.alma_client import AlmaClient
from aim.digifeeds.db_client import DBClient
from requests.exceptions import HTTPError


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

    @property
    def barcode(self) -> str:
        """The barcode of the Digifeeds item.

        Returns:
            str: The barcode.
        """
        return self.data["barcode"]

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


# TODO
def get_item(barcode: str) -> Item:
    return Item(DBClient().get_or_add_item(barcode))
