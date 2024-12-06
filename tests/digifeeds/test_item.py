import pytest
import json
import responses
from datetime import datetime, timedelta
from aim.digifeeds.item import (
    Item,
    process_item,
    rclone,
    DBClient,
    NotAddedToDigifeedsSetError,
)
from requests.exceptions import HTTPError
from aim.services import S


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def item_in_zephir_for_long_enough(item_data):
    zephir_status = {
        "name": "in_zephir",
        "description": "Item is in zephir",
        "created_at": "2024-09-25T17:13:28",
    }
    item_data["statuses"].append(zephir_status)
    return item_data


@pytest.fixture
def item_in_zephir_too_recent(item_in_zephir_for_long_enough):
    item_in_zephir_for_long_enough["statuses"][1]["created_at"] = (
        datetime.now().isoformat(timespec="seconds")
    )
    return item_in_zephir_for_long_enough


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


def test_move_to_pickup_success(mocker, item_in_zephir_for_long_enough):
    rclone_copyto_mock = mocker.patch.object(rclone, "copyto")
    rclone_moveto_mock = mocker.patch.object(rclone, "moveto")
    add_status_mock = mocker.patch.object(
        DBClient,
        "add_item_status",
        return_value=item_in_zephir_for_long_enough,
    )

    item = Item(item_in_zephir_for_long_enough)
    result = item.move_to_pickup()

    rclone_copyto_mock.assert_called_once()
    rclone_moveto_mock.assert_called_once()
    assert add_status_mock.call_count == 3
    assert result is not None


def test_move_to_pickup_item_too_recent(item_in_zephir_too_recent):
    item = Item(item_in_zephir_too_recent)
    result = item.move_to_pickup()

    assert result is None


def test_process_item_not_added_to_digifeeds_set_and_not_found_in_alma(
    mocker, item_data
):
    item_data["statuses"][0]["name"] = "not_found_in_alma"
    item = Item(item_data)

    item_mock = mocker.MagicMock(Item)
    item_mock.barcode.return_value = "some_barcode"
    item_mock.add_to_digifeeds_set.return_value = item

    with pytest.raises(Exception) as exc_info:
        process_item(item_mock)
    assert exc_info.type is NotAddedToDigifeedsSetError


def test_process_item_not_in_zephir_long_enough(item_in_zephir_too_recent):
    item = Item(item_in_zephir_too_recent)
    result = process_item(item)
    assert result is None


def test_process_item_not_in_zephir(mocker):
    item_mock = mocker.MagicMock(Item)
    item_mock.barcode.return_value = "some_barcode"
    item_mock.add_to_digifeeds_set.return_value = item_mock
    item_mock.check_zephir.return_value = None

    result = process_item(item_mock)
    assert result is None


def test_process_item_move_to_pickup(mocker):
    item_mock = mocker.MagicMock(Item)
    item_mock.barcode.return_value = "some_barcode"
    item_mock.add_to_digifeeds_set.return_value = item_mock
    item_mock.check_zephir.return_value = item_mock
    item_mock.move_to_pickup.return_value = item_mock

    result = process_item(item_mock)
    assert result is None
