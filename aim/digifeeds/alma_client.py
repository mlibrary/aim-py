import httpx2
from aim.services import S
import xml.etree.ElementTree as ET


class AlmaClient:
    def __init__(self) -> None:
        self.base_url = S.alma_api_url
        self.digifeeds_set_id = S.digifeeds_set_id
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
        url = self._url(f"conf/sets/{self.digifeeds_set_id}")
        query = {
            "id_type": "BARCODE",
            "op": "add_members",
            "fail_on_invalid_id": "true",
        }
        body = {"members": {"member": [{"id": barcode}]}}
        with httpx2.Client() as client:
            try:
                response = client.post(url, params=query, json=body)
                response.raise_for_status()
            except httpx2.HTTPError as e:
                if response.headers["content-type"] != "application/json":
                    S.logger.error(
                        f"HTTP error occurred: {e} {self.get_error_string(response.text)}"
                    )
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
