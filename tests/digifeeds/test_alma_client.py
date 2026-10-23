import pytest
import httpx2
from aim.services import S
from aim.digifeeds.alma_client import AlmaClient


@pytest.fixture
def alma_error_string():
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<web_service_result xmlns="http://com/exlibris/urm/general/xmlbeans">\r\n            <errorsExist>true</errorsExist>\r\n            <errorList>\r\n                        <error>\r\n                                    <errorCode>UNAUTHORIZED</errorCode>\r\n                                    <errorMessage>API-key not defined or not configured to allow this API.</errorMessage>\r\n                        </error>\r\n            </errorList>\r\n</web_service_result>'


def test_add_barcode_to_digifeeds_set_success(httpx2_mock):
    url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    query = {"id_type": "BARCODE", "op": "add_members", "fail_on_invalid_id": "true"}
    body = {"members": {"member": [{"id": "my_barcode"}]}}
    httpx2_mock.post(
        url,
        json=body,
        params=query,
    ).respond(200)
    response = AlmaClient().add_barcode_to_digifeeds_set("my_barcode")
    assert response is None


def test_add_barcode_to_digifeeds_set_failure(httpx2_mock, alma_error_string):
    url = f"{S.alma_api_url}/conf/sets/{S.digifeeds_set_id}"
    httpx2_mock.post(url).respond(500, text=alma_error_string)
    with pytest.raises(httpx2.HTTPError) as exc_info:
        AlmaClient().add_barcode_to_digifeeds_set("my_barcode")
    assert exc_info.type is httpx2.HTTPStatusError
