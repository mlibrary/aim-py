import requests
from aim.services import S
import xml.etree.ElementTree as ET
import sys, httpx2

sys.modules["httpx"] = httpx2  # do this first, before importing httpx or httpx_retries
import httpx  # -> httpx2
from httpx_retries import RetryTransport, Retry


class AlmaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "content": "application/json",
                "Accept": "application/json",
                "Authorization": f"apikey {S.alma_api_key}",
            }
        )
        self.base_url = S.alma_api_url
        self.headers = {
            "content": "application/json",
            "Accept": "application/json",
            "Authorization": f"apikey {S.alma_api_key}",
        }

    def get_barcode(self, barcode):
        url = f"{self.base_url}/items"
        query = {"item_barcode": barcode}
        retry = Retry(total=4, backoff_factor=5)
        transport = RetryTransport(retry=retry)
        with httpx2.Client(headers=self.headers, transport=transport) as client:
            try:
                response = client.get(url, params=query)
                response.raise_for_status()
                return response.json()

            except httpx2.HTTPError:
                if response.headers["Content-Type"].startswith("application/json"):
                    code = response.json()["errorList"]["error"][0]["errorCode"]
                    if code == "401689":
                        return {"not_found": True}
                        S.logger.error(f"Barcode not found: {barcode}")
                    else:
                        S.logger.error(f"Error code: {code} for barcode: {barcode}")
                else:
                    error = self.parse_error(response.text)
                    S.logger.error(
                        f"Error code: {error['code'].text}; Error message: {error['message'].text}; for barcode: {barcode}"
                    )
                    response.raise_for_status()

    def parse_error(self, error_string):
        ns = {"alma": "http://com/exlibris/urm/general/xmlbeans"}
        root = ET.fromstring(error_string)
        result = {}
        for error in root.findall(".//alma:error", ns):
            result["code"] = error.find("alma:errorCode", ns)
            result["message"] = error.find("alma:errorMessage", ns)
        return result
