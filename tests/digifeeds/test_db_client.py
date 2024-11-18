import responses
from responses import matchers
import pytest
from aim.services import S
from aim.digifeeds.db_client import DBClient
from requests.exceptions import HTTPError
import json
import copy


@pytest.fixture
def item_list():
    with open("tests/fixtures/digifeeds/item_list.json") as f:
        output = json.load(f)
    return output


@responses.activate
def test_get_item_success():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=200)
    item = DBClient().get_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_get_item_not_found():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=404)
    item = DBClient().get_item(barcode="my_barcode")
    assert item is None


@responses.activate
def test_get_item_raises_error():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=500)
    with pytest.raises(Exception) as exc_info:
        DBClient().get_item(barcode="my_barcode")
    assert exc_info.type is HTTPError


@responses.activate
def test_add_item_success():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.post(url, json={"item": "my_item"}, status=200)
    item = DBClient().add_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_add_item_failure():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.post(url, json={"item": "my_item"}, status=404)
    with pytest.raises(Exception) as exc_info:
        DBClient().add_item(barcode="my_barcode")
    assert exc_info.type is HTTPError


@responses.activate
def test_get_or_add_item_for_existing_item():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.get(url, json={"item": "my_item"}, status=200)
    item = DBClient().get_or_add_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_get_or_add_item_for_new_item():
    url = f"{S.digifeeds_api_url}/items/my_barcode"
    responses.get(url, json={}, status=404)
    responses.post(url, json={"item": "my_item"}, status=200)
    item = DBClient().get_or_add_item(barcode="my_barcode")
    assert item == {"item": "my_item"}


@responses.activate
def test_add_item_status_success():
    url = f"{S.digifeeds_api_url}/items/my_barcode/status/in_zephir"
    responses.put(url, json={"item": "my_item"}, status=200)
    item = DBClient().add_item_status(barcode="my_barcode", status="in_zephir")
    assert item == {"item": "my_item"}


@responses.activate
def test_add_item_status_failure():
    url = f"{S.digifeeds_api_url}/items/my_barcode/status/in_zephir"
    responses.put(url, json={}, status=500)
    with pytest.raises(Exception) as exc_info:
        DBClient().add_item_status(barcode="my_barcode", status="in_zephir")
    assert exc_info.type is HTTPError


@responses.activate
def test_get_items_multiple_pages(item_list):
    page_2 = copy.copy(item_list)
    page_2["offset"] = 1
    page_2["items"][0]["barcode"] = "some_other_barcode"
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        match=[matchers.query_param_matcher({"limit": 1, "offset": 0})],
        json=item_list,
    )
    responses.get(
        url=url,
        match=[matchers.query_param_matcher({"limit": 1, "offset": 1})],
        json=page_2,
    )

    items = DBClient().get_items(limit=1)
    assert (len(items)) == 2


@responses.activate
def test_get_items_in_zephir_value(item_list):
    item_list["total"] = 1
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        match=[
            matchers.query_param_matcher({"limit": 1, "offset": 0, "in_zephir": False})
        ],
        json=item_list,
    )
    items = DBClient().get_items(limit=1, in_zephir=False)
    assert (len(items)) == 1


@responses.activate
def test_get_items_fail_first_page():
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        status=500,
        match=[matchers.query_param_matcher({"limit": 1, "offset": 0})],
        json={},
    )

    with pytest.raises(Exception) as exc_info:
        DBClient().get_items(limit=1)

    assert exc_info.type is HTTPError


@responses.activate
def test_get_items_fail_later_page(item_list):
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        match=[matchers.query_param_matcher({"limit": 1, "offset": 0})],
        json=item_list,
    )
    responses.get(
        url=url,
        status=500,
        match=[matchers.query_param_matcher({"limit": 1, "offset": 1})],
        json={},
    )

    with pytest.raises(Exception) as exc_info:
        DBClient().get_items(limit=1)

    assert exc_info.type is HTTPError
