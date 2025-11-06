import requests
from aim.services import S


class Client:
    def get_item(self, htid: str):
        """Get an item from the Hathifiles Database

        Args:
            htid (str): HathiTrust id for the item

        Returns:
            json: A response object
        """
        url = self._url(f"items/{htid}")
        response = requests.get(url)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def _url(self, path) -> str:
        return f"{S.hathifiles_api_url}/{path}"
