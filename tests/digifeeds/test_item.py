import pytest
import json
import responses
from datetime import datetime, timedelta
from aim.digifeeds.item import Item
from aim.digifeeds.db_client import DBClient
from requests.exceptions import HTTPError
from aim.services import S


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def barcode():
    return "some_barcode"


def test_has_status_is_true(item_data):
    result = Item(item_data).has_status("added_to_digifeeds_set")
    assert result is True


def test_has_status_is_false(item_data):
    result = Item(item_data).has_status("in_zephir")
    assert result is False


def test_in_zephir_for_long_enough_is_true(item_data):
    item_data["statuses"][0]["name"] = "in_zephir"
    over_two_weeks_ago = datetime.now() - timedelta(days=15)
    item_data["statuses"][0]["created_at"] = over_two_weeks_ago.isoformat(
        timespec="seconds"
    )
    result = Item(item_data).in_zephir_for_long_enough
    assert result is True


def test_in_zephir_for_long_enough_is_false(item_data):
    item_data["statuses"][0]["name"] = "in_zephir"
    less_than_two_weeks_ago = datetime.now() - timedelta(days=13)
    item_data["statuses"][0]["created_at"] = less_than_two_weeks_ago.isoformat(
        timespec="seconds"
    )
    result = Item(item_data).in_zephir_for_long_enough
    assert result is False


def test_in_zephir_for_long_enough_when_not_in_zephir(item_data):
    result = Item(item_data).in_zephir_for_long_enough
    assert result is False


def test_add_to_digifeeds_set_for_barcode_thats_in_the_digifeeds_set(item_data):
    item = Item(item_data)
    result = item.add_to_digifeeds_set()
    assert result == item


@responses.activate
def test_add_to_digifeeds_set_where_item_is_in_the_digifeeds_set_but_doesnt_have_status(
    mocker, item_data
):
    item_data["statuses"][0]["name"] = "some_other_status"
    item = Item(item_data)
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )
    error_body = {
        "errorsExist": True,
        "errorList": {
            "error": [
                {
                    "errorCode": "60115",
                    "errorMessage": "The following ID(s) are already in the set ['some_barcode']",
                    "trackingId": "E01-2609211329-8EKLP-AWAE1781893571",
                }
            ]
        },
    }
    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_set_stub = responses.post(
        add_to_digifeeds_url,
        json=error_body,
        status=400,
    )

    result = item.add_to_digifeeds_set()
    add_status_mock.assert_called_once_with(
        barcode="some_barcode", status="added_to_digifeeds_set"
    )
    assert add_to_digifeeds_set_stub.call_count == 1
    assert result.barcode == item.barcode


@responses.activate
def test_add_to_digifeeds_set_for_barcode_thats_not_in_the_digifeeds_set(
    mocker, item_data
):
    item_data["statuses"][0]["name"] = "some_other_status"
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )
    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_set_stub = responses.post(
        add_to_digifeeds_url,
        json=item_data,
        status=200,
    )
    item = Item(item_data)
    result = item.add_to_digifeeds_set()

    add_status_mock.assert_called_once()
    assert add_to_digifeeds_set_stub.call_count == 1
    assert result.barcode == item.barcode


@responses.activate
def test_add_to_digifeeds_set_barcode_that_is_not_in_alma(mocker, item_data):
    item_data["statuses"][0]["name"] = "some_other_status"
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )
    error_body = {
        "errorsExist": True,
        "errorList": {
            "error": [
                {
                    "errorCode": "60120",
                    "errorMessage": "The ID whatever is not valid for content type ITEM and identifier type BARCODE.",
                    "trackingId": "E01-2609211329-8EKLP-AWAE1781893571",
                }
            ]
        },
    }
    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_set_stub = responses.post(
        add_to_digifeeds_url,
        json=error_body,
        status=400,
    )

    item = Item(item_data)
    result = item.add_to_digifeeds_set()
    add_status_mock.assert_called_once_with(
        barcode="some_barcode", status="not_found_in_alma"
    )
    assert add_to_digifeeds_set_stub.call_count == 1
    assert result.barcode == item.barcode


@responses.activate
def test_add_to_digifeeds_set_barcode_that_causes_alma_error(mocker, item_data):
    item_data["statuses"][0]["name"] = "some_other_status"
    add_status_mock = mocker.patch.object(DBClient, "add_item_status")
    error_body = {
        "errorsExist": True,
        "errorList": {
            "error": [
                {
                    "errorCode": "60125",
                    "errorMessage": "some_other_error",
                    "trackingId": "E01-2609211329-8EKLP-AWAE1781893571",
                }
            ]
        },
    }
    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_set_stub = responses.post(
        add_to_digifeeds_url,
        json=error_body,
        status=400,
    )

    item = Item(item_data)
    with pytest.raises(Exception) as exc_info:
        item.add_to_digifeeds_set()
    assert exc_info.type is HTTPError
    assert add_to_digifeeds_set_stub.call_count == 1
    add_status_mock.assert_not_called()


@responses.activate
def test_barcode_is_in_zephir(mocker, item_data, barcode):
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )

    responses.get(f"{S.zephir_bib_api_url}/mdp.{barcode}", json={}, status=200)
    item = Item(item_data)
    result = item.check_zephir()
    add_status_mock.assert_called_once()
    assert result.barcode == barcode


def test_barcode_already_has_in_zephir_status(mocker, item_data):
    item_data["statuses"][0]["name"] = "in_zephir"

    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )

    item = Item(item_data)
    result = item.check_zephir()
    add_status_mock.assert_not_called()
    assert result.barcode == item.barcode


@responses.activate
def test_barcode_not_in_zephir(mocker, item_data, barcode):
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )
    responses.get(f"{S.zephir_bib_api_url}/mdp.{barcode}", json={}, status=404)

    item = Item(item_data)
    result = item.check_zephir()
    add_status_mock.assert_not_called()
    assert result is None
