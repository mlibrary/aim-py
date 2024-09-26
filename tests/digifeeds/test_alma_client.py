import responses
from responses import matchers
import pytest
from aim.services import S
from aim.digifeeds.alma_client import AlmaClient
from requests.exceptions import HTTPError


@pytest.fixture
def alma_base_url():
    return "https://api-na.hosted.exlibrisgroup.com/almaws/v1"


@responses.activate
def test_add_barcode_to_digifeeds_set_success(alma_base_url):
    url = f"{alma_base_url}/conf/sets/{S.digifeeds_set_id}"
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
def test_add_barcode_to_digifeeds_set_failure(alma_base_url):
    url = f"{alma_base_url}/conf/sets/{S.digifeeds_set_id}"
    responses.post(
        url,
        json={},
        status=500,
    )
    with pytest.raises(Exception) as exc_info:
        AlmaClient().add_barcode_to_digifeeds_set("my_barcode")
    assert exc_info.type is HTTPError
