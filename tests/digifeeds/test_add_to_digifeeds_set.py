# from unittest.mock import patch
# # from aim.digifeeds.alma_client import AlmaClient
import json
import pytest
import responses
from aim.digifeeds.functions import add_to_digifeeds_set
from aim.digifeeds.alma_client import AlmaClient
from aim.digifeeds.db_client import DBClient
from requests.exceptions import HTTPError
from aim.services import S


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


def test_add_to_digifeeds_set_for_barcode_thats_in_the_digifeeds_set(mocker, item_data):
    get_item_mock = mocker.patch.object(
        DBClient, "get_or_add_item", return_value=item_data
    )
    result = add_to_digifeeds_set("my_barcode")
    get_item_mock.assert_called_once()
    assert result.barcode == "some_barcode"


@responses.activate
def test_add_to_db_barcode_thats_in_the_digifeeds_set_but_doesnt_have_status(
    mocker, item_data
):
    item_data["statuses"][0]["name"] = "some_other_status"
    get_item_mock = mocker.patch.object(
        DBClient, "get_or_add_item", return_value=item_data
    )
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

    result = add_to_digifeeds_set("some_barcode")
    get_item_mock.assert_called_once()
    add_status_mock.assert_called_once_with(
        barcode="some_barcode", status="added_to_digifeeds_set"
    )
    assert add_to_digifeeds_set_stub.call_count == 1
    assert result.barcode == "some_barcode"


def test_add_to_digifeeds_set_for_barcode_thats_not_in_the_digifeeds_set(
    mocker, item_data
):
    item_data["statuses"][0]["name"] = "some_other_status"
    get_item_mock = mocker.patch.object(
        DBClient, "get_or_add_item", return_value=item_data
    )
    add_status_mock = mocker.patch.object(
        DBClient, "add_item_status", return_value=item_data
    )
    add_to_digifeeds_set_mock = mocker.patch.object(
        AlmaClient,
        "add_barcode_to_digifeeds_set",
        return_value=item_data,
    )
    result = add_to_digifeeds_set("some_barcode")
    get_item_mock.assert_called_once()
    add_status_mock.assert_called_once()
    add_to_digifeeds_set_mock.assert_called_once()
    assert result.barcode == "some_barcode"


@responses.activate
def test_add_to_digifeeds_set_barcode_that_is_not_in_alma(mocker, item_data):
    item_data["statuses"][0]["name"] = "some_other_status"
    get_item_mock = mocker.patch.object(
        DBClient, "get_or_add_item", return_value=item_data
    )
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

    result = add_to_digifeeds_set("some_barcode")
    get_item_mock.assert_called_once()
    add_status_mock.assert_called_once_with(
        barcode="some_barcode", status="not_found_in_alma"
    )
    assert add_to_digifeeds_set_stub.call_count == 1
    assert result.barcode == "some_barcode"


@responses.activate
def test_add_to_digifeeds_set_barcode_that_causes_alma_error(mocker, item_data):
    item_data["statuses"][0]["name"] = "some_other_status"
    get_item_mock = mocker.patch.object(
        DBClient, "get_or_add_item", return_value=item_data
    )
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

    with pytest.raises(Exception) as exc_info:
        add_to_digifeeds_set("my_barcode")
    assert exc_info.type is HTTPError
    assert add_to_digifeeds_set_stub.call_count == 1
    get_item_mock.assert_called_once()
    add_status_mock.assert_not_called()