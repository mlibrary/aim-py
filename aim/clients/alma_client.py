import httpx2
from aim.services import S
import xml.etree.ElementTree as ET
import sys

sys.modules["httpx"] = httpx2  # do this first, before importing httpx or httpx_retries
from httpx_retries import RetryTransport, Retry


class AlmaClient:
    def __init__(self) -> None:
        self.base_url = S.alma_api_url
        self.headers = {
            "Authorization": f"apikey {S.alma_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def add_barcode_to_digifeeds_set(self, barcode: str) -> None:
        """Adds a barcode to the digifeeds set in Alma

        Args:
            barcode (str): Barcode of the item

        Returns:
            None: None
        """
        url = self._url(f"conf/sets/{S.digifeeds_set_id}")
        query = {
            "id_type": "BARCODE",
            "op": "add_members",
            "fail_on_invalid_id": "true",
        }
        body = {"members": {"member": [{"id": barcode}]}}
        with httpx2.Client(headers=self.headers) as client:
            try:
                response = client.post(url, params=query, json=body)
                response.raise_for_status()
            except httpx2.HTTPError as e:
                if not response.headers["Content-Type"].startswith("application/json"):
                    S.logger.error(
                        f"HTTP error occurred: {e} {self.get_error_string(response.text)}"
                    )
                raise

    def get_barcode(self, barcode):
        url = f"{self.base_url}/items"
        query = {"item_barcode": barcode}
        retry = Retry(total=4, backoff_factor=5)
        transport = RetryTransport(retry=retry)
        with httpx2.Client(
            headers=self.headers, transport=transport, follow_redirects=True
        ) as client:
            try:
                response = client.get(url, params=query)
                response.raise_for_status()
                return response.json()

            except httpx2.HTTPError as e:
                if response.headers["Content-Type"].startswith("application/json"):
                    code = response.json()["errorList"]["error"][0]["errorCode"]
                    if code == "401689":
                        return {"not_found": True}
                        S.logger.error(f"Barcode not found: {barcode}")
                    else:
                        S.logger.error(f"Error code: {code} for barcode: {barcode}")
                else:
                    S.logger.error(
                        "http_error",
                        message=f"HTTP error occurred: {e} {self.get_error_string(response.text)}",
                        status=response.status_code,
                        barcode=barcode,
                    )
                    raise

    def update_alma_item(
        self, mms_id: str, holding_id: str, item_pid: str, item_body: dict
    ):
        url = self._url(f"bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}")
        with httpx2.Client(headers=self.headers) as client:
            try:
                response = client.put(url, json=item_body)
                response.raise_for_status()
                return response.json()
            except httpx2.HTTPError as e:
                if response.headers["Content-Type"].startswith("application/json"):
                    S.logger.error(
                        "http_error",
                        message=f"HTTP error occurred: {e} {self.get_error_string(response.text)}",
                        status=response.status_code,
                        item_pid=item_pid,
                    )
                else:
                    S.logger.error(f"HTTP error occurred: {e} {response.json()}")
                raise

    def get_error_string(self, error_string):
        ns = {"alma": "http://com/exlibris/urm/general/xmlbeans"}
        root = ET.fromstring(error_string)
        result = []
        for error in root.findall(".//alma:error", ns):
            code = error.find("alma:errorCode", ns)
            message = error.find("alma:errorMessage", ns)
            result.append(f"code: {code.text}, message: {message.text}")

        return " | ".join(result)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path}"
