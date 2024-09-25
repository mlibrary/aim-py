import requests
from aim.services import S


class DBClient:
    def get_item(self, barcode: str):
        url = f"{S.digifeeds_api_url}/{barcode}"
        print(url)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            response.raise_for_status()

    def add_item(self, barcode: str):
        response = requests.post(f"{S.digifeeds_api_url}/{barcode}")
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
