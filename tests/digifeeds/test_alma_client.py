import responses
from responses import matchers
import pytest
from aim.services import S
from aim.digifeeds.alma_client import AlmaClient
from requests.exceptions import HTTPError


@responses.activate
def test_add_barcode_to_digifeeds_set_success():
    url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    query = {"id_type": "BARCODE", "op": "add_members", "fail_on_invalid_id": "true"}
    body = {"members": {"member": [{"id": "my_barcode"}]}}
    responses.post(
        url,
        match=[
            matchers.query_param_matcher(query),
            matchers.json_params_matcher(body),
        ],
        json={},
        status=200,
    )
    response = AlmaClient().add_barcode_to_digifeeds_set("my_barcode")
    assert response is None


@responses.activate
def test_add_barcode_to_digifeeds_set_failure():
    url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    responses.post(
        url,
        json={},
        status=500,
    )
    with pytest.raises(Exception) as exc_info:
        AlmaClient().add_barcode_to_digifeeds_set("my_barcode")
    assert exc_info.type is HTTPError
