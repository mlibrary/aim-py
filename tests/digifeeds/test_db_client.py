import responses
import pytest
from aim.services import S
from aim.digifeeds.db_client import DBClient
from requests.exceptions import HTTPError


@responses.activate
def test_get_item_success():
    url = f"{S.digifeeds_api_url}/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=200)
    item = DBClient().get_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_get_item_not_found():
    url = f"{S.digifeeds_api_url}/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=404)
    item = DBClient().get_item(barcode="my_barcode")
    assert item == None


@responses.activate
def test_get_item_raises_error():
    url = f"{S.digifeeds_api_url}/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=500)
    with pytest.raises(Exception) as exc_info:
        DBClient().get_item(barcode="my_barcode")
    assert exc_info.type is HTTPError


@responses.activate
def test_add_item_success():
    url = f"{S.digifeeds_api_url}/my_barcode"
    responses.post(url, json={"item": "my_item"}, status=200)
    item = DBClient().add_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_add_item_failure():
    url = f"{S.digifeeds_api_url}/my_barcode"
    responses.post(url, json={"item": "my_item"}, status=404)
    with pytest.raises(Exception) as exc_info:
        DBClient().add_item(barcode="my_barcode")
    assert exc_info.type is HTTPError
