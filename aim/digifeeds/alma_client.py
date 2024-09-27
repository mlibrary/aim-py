import requests
from aim.services import S


class AlmaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "content": "application/json",
                "Accept": "application/json",
                "Authorization": f"apikey { S.alma_api_key }",
            }
        )
        self.base_url = S.alma_api_url
        self.digifeeds_set_id = S.digifeeds_set_id

    def add_barcode_to_digifeeds_set(self, barcode: str) -> None:
        url = self._url(f"conf/sets/{self.digifeeds_set_id}")
        query = {
            "id_type": "BARCODE",
            "op": "add_members",
            "fail_on_invalid_id": "true",
        }
        body = {"members": {"member": [{"id": barcode}]}}
        response = self.session.post(url, params=query, json=body)
        if response.status_code != 200:
            response.raise_for_status()
        return None

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path}"
