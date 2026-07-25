import requests
from urllib3.util import Retry
from aim.services import S
import xml.etree.ElementTree as ET


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
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            allowed_methods={"GET"},
        )
        self.session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=retries)
        )
        self.base_url = S.alma_api_url

    def get_barcode(self, barcode):
        url = f"{self.base_url}/items"
        query = {"item_barcode": barcode}
        try:
            response = self.session.get(url, params=query)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError:
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

    def parse_error(self, error_string):
        ns = {"alma": "http://com/exlibris/urm/general/xmlbeans"}
        root = ET.fromstring(error_string)
        result = {}
        for error in root.findall(".//alma:error", ns):
            result["code"] = error.find("alma:errorCode", ns)
            result["message"] = error.find("alma:errorMessage", ns)
        return result
