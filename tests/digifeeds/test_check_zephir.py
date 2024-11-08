import pytest
import responses
import json
from aim.services import S
from aim.digifeeds.check_zephir import check_zephir


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def barcode():
    return "some_barcode"


@responses.activate
def test_barcode_is_in_zephir(mocker, item_data, barcode):
    get_item_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.get_item", return_value=item_data
    )
    add_status_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.add_item_status", return_value=item_data
    )

    responses.get(f"{S.zephir_bib_api_url}/mdp.{barcode}", json={}, status=200)
    result = check_zephir(barcode)
    get_item_mock.assert_called_once()
    add_status_mock.assert_called_once()
    assert result.barcode == barcode


def test_barcode_already_has_in_zephir_status(mocker, item_data, barcode):
    item_data["statuses"][0]["name"] = "in_zephir"
    get_item_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.get_item", return_value=item_data
    )

    add_status_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.add_item_status", return_value=item_data
    )

    result = check_zephir(barcode)
    get_item_mock.assert_called_once()
    add_status_mock.assert_not_called()
    assert result.barcode == barcode


@responses.activate
def test_barcode_not_in_zephir(mocker, item_data, barcode):
    get_item_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.get_item", return_value=item_data
    )
    add_status_mock = mocker.patch(
        "aim.digifeeds.check_zephir.DBClient.add_item_status", return_value=item_data
    )

    responses.get(f"{S.zephir_bib_api_url}/mdp.{barcode}", json={}, status=404)
    result = check_zephir(barcode)
    get_item_mock.assert_called_once()
    add_status_mock.assert_not_called()
    assert result is None


def test_barcdoe_is_not_in_db(mocker, barcode):
    mocker.patch("aim.digifeeds.check_zephir.DBClient.get_item", return_value=None)
    with pytest.raises(Exception) as exc_info:
        check_zephir(barcode)
    assert exc_info.type is Exception
