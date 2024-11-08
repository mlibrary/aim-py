import requests
from aim.services import S


class DBClient:
    def __init__(self) -> None:
        self.base_url = S.digifeeds_api_url

    def get_item(self, barcode: str):
        """Get an item from the digifeeds database

        Args:
            barcode (str): Barcode of the item

        Returns:
            json: A response object
        """
        url = self._url(f"items/{barcode}")
        response = requests.get(url)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def add_item(self, barcode: str):
        """Add an item to the digifeeds database

        Args:
            barcode (str): Barcode of the item

        Returns:
            json: A response object
        """
        url = self._url(f"items/{barcode}")
        response = requests.post(url)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def get_or_add_item(self, barcode: str):
        """Gets or adds an item to the digifeeds database

        Args:
            barcode (str): Barcode of the item

        Returns:
            Object: An item
        """
        item = self.get_item(barcode)
        if not item:
            item = self.add_item(barcode)
        return item

    def add_item_status(self, barcode: str, status: str):
        """Add a status to an item in the database

        Args:
            barcode (str): Barcode of the item
            status (str): Status to add

        Returns:
            json: A response object
        """
        url = self._url(f"items/{barcode}/status/{status}")
        response = requests.put(url)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def _url(self, path) -> str:
        return f"{self.base_url}/{path}"
