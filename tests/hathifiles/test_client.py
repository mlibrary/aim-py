import responses
from aim.services import S
from aim.hathifiles.client import Client
from requests.exceptions import HTTPError
import pytest


@responses.activate
def test_get_item_success():
    url = f"{S.hathifiles_api_url}/items/my_htid"
    responses.get(url, json={"item": "my_item"}, status=200)
    item = Client().get_item(htid="my_htid")
    assert item == {"item": "my_item"}


@responses.activate
def test_get_item_not_found():
    url = f"{S.hathifiles_api_url}/items/my_htid"
    responses.get(url, json={"item": "my_item"}, status=404)
    item = Client().get_item(htid="my_htid")
    assert item is None


@responses.activate
def test_get_item_raises_error():
    url = f"{S.hathifiles_api_url}/items/my_htid"
    responses.get(url, json={"item": "my_item"}, status=500)
    with pytest.raises(Exception) as exc_info:
        Client().get_item(htid="my_htid")
    assert exc_info.type is HTTPError
