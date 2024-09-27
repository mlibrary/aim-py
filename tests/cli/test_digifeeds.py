import responses
import pytest
import json
from responses import matchers
from typer.testing import CliRunner
from aim.cli.main import app
from aim.services import S

runner = CliRunner()


@pytest.fixture
def item_data():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@responses.activate
def test_add_to_db_where_item_is_not_in_digifeeds_set(item_data):
    item_data["statuses"][0]["name"] = "in_zephir"
    get_add_url = f"{S.digifeeds_api_url}/items/some_barcode"

    get_item = responses.get(get_add_url, json={}, status=404)
    post_item = responses.post(get_add_url, json=item_data, status=200)
    add_item_status = responses.put(
        f"{get_add_url}/status/added_to_digifeeds_set", json=item_data, status=200
    )

    add_to_digifeeds_url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    add_to_digifeeds_query = {
        "id_type": "BARCODE",
        "op": "add_members",
        "fail_on_invalid_id": "true",
    }
    add_to_digifeeds_body = {"members": {"member": [{"id": "some_barcode"}]}}
    add_to_digifeeds_set = responses.post(
        add_to_digifeeds_url,
        match=[
            matchers.query_param_matcher(add_to_digifeeds_query),
            matchers.json_params_matcher(add_to_digifeeds_body),
        ],
        json={},
        status=200,
    )

    result = runner.invoke(app, ["digifeeds", "add-to-db", "some_barcode"])
    assert get_item.call_count == 1
    assert post_item.call_count == 1
    assert add_to_digifeeds_set.call_count == 1
    assert add_item_status.call_count == 1
    assert result.exit_code == 0
    assert 'Adding barcode "some_barcode" to database' in result.stdout


def test_load_statuses(mocker):
    session_local_mock = mocker.patch("aim.digifeeds.database.main.SessionLocal")
    load_statuse_mock = mocker.patch("aim.digifeeds.database.models.load_statuses")
    result = runner.invoke(app, ["digifeeds", "load-statuses"])
    assert session_local_mock.call_count == 1
    assert load_statuse_mock.call_count == 1
    assert result.exit_code == 0
