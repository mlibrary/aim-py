import requests
from aim.services import S


class DBClient:
    def __init__(self) -> None:
        self.base_url = S.digifeeds_api_url

    def get_item(self, barcode: str):
        url = self._url(f"items/{barcode}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            response.raise_for_status()

    def add_item(self, barcode: str):
        url = self._url(f"items/{barcode}")
        response = requests.post(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_or_add_item(self, barcode: str):
        item = self.get_item(barcode)
        if not item:
            item = self.add_item(barcode)
        return item

    def add_item_status(self, barcode: str, status: str):
        url = self._url(f"items/{barcode}/status/{status}")
        response = requests.put(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def _url(self, path) -> str:
        return f"{self.base_url}/{path}"
