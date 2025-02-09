import responses
import pytest
import json
from responses import matchers
from typer.testing import CliRunner
from aim.cli.main import app
from aim.services import S
from aim.digifeeds.item import Item
from aim.digifeeds import functions
from datetime import datetime

runner = CliRunner()


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def item_in_zephir_too_recent(item_data):
    zephir_status = {
        "name": "in_zephir",
        "description": "Item is in zephir",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    item_data["statuses"].append(zephir_status)
    return item_data


@responses.activate
def test_add_to_db_where_item_is_not_in_digifeeds_set(item_data):
    item_data["statuses"][0]["name"] = "in_zephir"
    get_add_url = f"{S.digifeeds_api_url}/items/some_barcode"

    get_item = responses.get(get_add_url, json={}, status=404)
    post_item = responses.post(get_add_url, json=item_data, status=200)
    more_statuses = item_data.copy()
    more_statuses["statuses"].append({"name": "added_to_digifeeds_set"})
    add_item_status = responses.put(
        f"{get_add_url}/status/added_to_digifeeds_set", json=more_statuses, status=200
    )

    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_query = {
        "id_type": "BARCODE",
        "op": "add_members",
        "fail_on_invalid_id": "true",
    }
    add_to_digifeeds_body = {"members": {"member": [{"id": "some_barcode"}]}}
    add_to_digifeeds_set_stub = responses.post(
        add_to_digifeeds_url,
        match=[
            matchers.query_param_matcher(add_to_digifeeds_query),
            matchers.json_params_matcher(add_to_digifeeds_body),
        ],
        json={},
        status=200,
    )

    result = runner.invoke(app, ["digifeeds", "add-to-digifeeds-set", "some_barcode"])
    assert get_item.call_count == 1
    assert post_item.call_count == 1
    assert add_to_digifeeds_set_stub.call_count == 1
    assert add_item_status.call_count == 1
    assert result.exit_code == 0
    assert "add_to_digifeeds_set_start" in result.stdout
    assert "added_to_digifeeds_set" in result.stdout


def test_add_to_db_where_item_is_not_in_alma(mocker):
    item_mock = mocker.MagicMock(Item)
    item_mock.has_status.side_effect = [True, False]
    item_mock.add_to_digifeeds_set.return_value = item_mock

    mocker.patch("aim.cli.digifeeds.get_item", return_value=item_mock)

    result = runner.invoke(app, ["digifeeds", "add-to-digifeeds-set", "some_barcode"])
    assert "not_found_in_alma" in result.stdout
    assert "not_added_to_digifeeds_set" in result.stdout


def test_load_statuses(mocker):
    session_local_mock = mocker.patch("aim.digifeeds.database.main.SessionLocal")
    load_statuse_mock = mocker.patch("aim.digifeeds.database.models.load_statuses")
    result = runner.invoke(app, ["digifeeds", "load-statuses"])
    assert session_local_mock.call_count == 1
    assert load_statuse_mock.call_count == 1
    assert result.exit_code == 0


def test_list_barcodes_in_input_bucket(mocker):
    list_barcodes_mock = mocker.patch.object(
        functions,
        "list_barcodes_in_input_bucket",
        return_value=["barcode1", "barcode2"],
    )
    result = runner.invoke(app, ["digifeeds", "list-barcodes-in-input-bucket"])
    assert list_barcodes_mock.call_count == 1
    assert result.exit_code == 0
    assert '["barcode1", "barcode2"]' == result.stdout


@responses.activate
def test_check_zephir_for_item_when_item_is_in_zephir(item_data):
    db_url = f"{S.digifeeds_api_url}/items/some_barcode"
    get_item = responses.get(db_url, json=item_data, status=200)
    add_item_status = responses.put(
        f"{db_url}/status/in_zephir", json=item_data, status=200
    )
    responses.get(f"{S.zephir_bib_api_url}/mdp.some_barcode", json={}, status=200)
    result = runner.invoke(app, ["digifeeds", "check-zephir", "some_barcode"])
    assert get_item.call_count == 1
    assert add_item_status.call_count == 1
    assert result.exit_code == 0
    assert "in_zephir" in result.stdout


@responses.activate
def test_check_zephir_for_item_when_item_is_not_in_zephir(item_data):
    db_url = f"{S.digifeeds_api_url}/items/some_barcode"
    get_item = responses.get(db_url, json=item_data, status=200)
    add_item_status = responses.put(f"{db_url}/status/in_zephir")
    responses.get(f"{S.zephir_bib_api_url}/mdp.some_barcode", json={}, status=404)
    result = runner.invoke(app, ["digifeeds", "check-zephir", "some_barcode"])
    assert get_item.call_count == 1
    assert add_item_status.call_count == 0
    assert result.exit_code == 0
    assert "not_in_zephir" in result.stdout


def test_move_to_pickup_success(mocker, item_data):
    item = Item(item_data)
    item_mock = mocker.MagicMock(Item)
    item_mock.move_to_pickup.return_value = item

    mocker.patch("aim.cli.digifeeds.get_item", return_value=item_mock)

    result = runner.invoke(app, ["digifeeds", "move-to-pickup", "some_barcode"])

    assert "move_to_pickup_success" in result.stdout
    assert result.exit_code == 0


def test_move_to_pickup_where_not_in_zephir(mocker):
    item_mock = mocker.MagicMock(Item)
    item_mock.move_to_pickup.return_value = None

    mocker.patch("aim.cli.digifeeds.get_item", return_value=item_mock)

    result = runner.invoke(app, ["digifeeds", "move-to-pickup", "some_barcode"])

    assert "not_in_zephir_long_enough" in result.stdout
    assert result.exit_code == 0


def test_process_barcode(mocker, item_in_zephir_too_recent):
    item = Item(item_in_zephir_too_recent)
    mocker.patch("aim.cli.digifeeds.get_item", return_value=item)

    result = runner.invoke(app, ["digifeeds", "process-barcode", "some_barcode"])

    assert "add_to_digifeeds_set_start" in result.stdout
    assert "added_to_digifeeds_set" in result.stdout
    assert "in_zephir" in result.stdout
    assert "not_in_zephir_long_enough" in result.stdout
    assert result.exit_code == 0


def test_process_barcodes(mocker, item_in_zephir_too_recent):
    item1 = Item(item_in_zephir_too_recent)
    data2 = item_in_zephir_too_recent.copy()
    data2["barcode"] = "other_barcode"
    item2 = Item(data2)

    mocker.patch("aim.cli.digifeeds.get_item", side_effect=[item1, item2])

    result = runner.invoke(
        app, ["digifeeds", "process-barcodes", "some_barcode", "other_barcode"]
    )

    assert "add_to_digifeeds_set_start" in result.stdout
    assert "added_to_digifeeds_set" in result.stdout
    assert "in_zephir" in result.stdout
    assert "not_in_zephir_long_enough" in result.stdout
    assert "some_barcode" in result.stdout
    assert "other_barcode" in result.stdout
    assert result.exit_code == 0


def test_generate_barcodes_in_s3_report(mocker):
    generate_report_mock = mocker.patch.object(
        functions, "generate_barcodes_added_in_last_two_weeks_report"
    )

    result = runner.invoke(app, ["digifeeds", "generate-barcodes-in-s3-report"])

    generate_report_mock.assert_called()

    assert result.exit_code == 0
