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
