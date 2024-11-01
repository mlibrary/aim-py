import pytest
import json
from datetime import datetime, timedelta
from aim.digifeeds.item import Item


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


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
