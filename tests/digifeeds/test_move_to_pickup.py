from aim.digifeeds.move_to_pickup import move_to_pickup, rclone, DBClient
import json
import pytest
from datetime import datetime


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def item_in_zephir_for_long_enough(item_data):
    item_data["statuses"][0]["name"] = "in_zephir"
    return item_data


@pytest.fixture
def item_in_zephir_too_recent(item_in_zephir_for_long_enough):
    item_in_zephir_for_long_enough["statuses"][0]["created_at"] = (
        datetime.now().isoformat(timespec="seconds")
    )
    return item_in_zephir_for_long_enough


def test_move_to_pickup_success(mocker, item_in_zephir_for_long_enough):
    rclone_copyto_mock = mocker.patch.object(rclone, "copyto")
    rclone_moveto_mock = mocker.patch.object(rclone, "moveto")
    get_item_mock = mocker.patch.object(
        DBClient,
        "get_item",
        return_value=item_in_zephir_for_long_enough,
    )
    add_status_mock = mocker.patch.object(
        DBClient,
        "add_item_status",
        return_value=item_in_zephir_for_long_enough,
    )

    result = move_to_pickup(item_in_zephir_for_long_enough["barcode"])

    get_item_mock.assert_called_once()
    rclone_copyto_mock.assert_called_once()
    rclone_moveto_mock.assert_called_once()
    assert add_status_mock.call_count == 3
    assert result is not None


def test_move_to_pickup_no_item(mocker):
    get_item_mock = mocker.patch.object(DBClient, "get_item", return_value=None)
    with pytest.raises(Exception) as exc_info:
        move_to_pickup("some_barcode")

    get_item_mock.assert_called_once()
    assert str(exc_info.value) == "Item not found in database"


def test_move_to_pickup_item_too_recent(mocker, item_in_zephir_too_recent):
    get_item_mock = mocker.patch.object(
        DBClient,
        "get_item",
        return_value=item_in_zephir_too_recent,
    )
    result = move_to_pickup(item_in_zephir_too_recent["barcode"])

    get_item_mock.assert_called_once()
    assert result is None
