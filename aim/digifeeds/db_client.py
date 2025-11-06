import requests
from aim.services import S
from datetime import datetime


class DBClient:
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

    def update_hathifiles_timestamp(self, barcode: str, timestamp: datetime):
        """
        Updates the hathifiles_timestamp field for an existing barcode

        Args:
            barcode (str): Barcode of the item
            timestamp (datetime): rights_timestamp value from Hathifiles DB

        Returns:
            json: A response object
        """
        url = self._url(f"items/{barcode}/hathifiles_timestamp/{timestamp.isoformat()}")
        response = requests.put(url)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def get_items(self, limit: int = 50, q: str | None = None) -> list:
        """
        Pages through all items to return a list. Takes an optional q string to
        filter the list of items

        Args:
            limit (int, optional): How many items to fetch with each page. Changing this still results in getting all matching results. Defaults to 50.
            q (str | None, optional): Query string that the api is expecting. Defaults to None.

        Returns:
            list: List of item objects.
        """
        items = []
        url = self._url("items")
        params = {
            "limit": limit,
            "offset": 0,
        }
        if q:
            params["q"] = q

        response = requests.get(url, params=params)
        if response.status_code != 200:
            response.raise_for_status()

        first_page = response.json()
        total = first_page["total"]
        for item in first_page["items"]:
            items.append(item)

        for offset in list(range(limit, total, limit)):
            params["offset"] = offset
            response = requests.get(url, params=params)
            if response.status_code != 200:
                response.raise_for_status()
            for item in response.json()["items"]:
                items.append(item)

        return items

    def _url(self, path) -> str:
        return f"{S.digifeeds_api_url}/{path}"
