from datetime import datetime, timedelta


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

    @property
    def barcode(self) -> str:
        """The barcode of the Digifeeds item.

        Returns:
            str: The barcode.
        """
        return self.data["barcode"]

    @property
    def in_zephir_for_long_enough(self) -> bool:
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
