import pytest
import json
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
