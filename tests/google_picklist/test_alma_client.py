import responses

import pytest
from aim.services import S
from aim.google_picklist.alma_client import AlmaClient
from httpx2 import HTTPStatusError


@pytest.fixture
def alma_error_string():
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<web_service_result xmlns="http://com/exlibris/urm/general/xmlbeans">\r\n            <errorsExist>true</errorsExist>\r\n            <errorList>\r\n                        <error>\r\n                                    <errorCode>UNAUTHORIZED</errorCode>\r\n                                    <errorMessage>API-key not defined or not configured to allow this API.</errorMessage>\r\n                        </error>\r\n            </errorList>\r\n</web_service_result>'


@responses.activate
def test_get_barcode_success(httpx2_mock):
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    httpx2_mock.get(url, params=query).respond(200, json={"success": "true"})
    response = AlmaClient().get_barcode("some_barcode")
    assert response == {"success": "true"}


@responses.activate
def test_get_barcode_not_found(httpx2_mock):
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    body = {
        "errorsExist": True,
        "errorList": {
            "error": [
                {
                    "errorCode": "401689",
                    "errorMessage": "No items found for barcode some_barcode.",
                    "trackingId": "E01-2507134129-Z0415-AWAE2086938389",
                }
            ]
        },
    }
    httpx2_mock.get(url, params=query).respond(400, json=body)
    response = AlmaClient().get_barcode("some_barcode")
    assert response == {"not_found": True}


@responses.activate
def test_get_barcode_retries_on_connection_problem(httpx2_mock):
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    response_body = "Error"
    rsp1 = httpx2_mock.get(url, params=query).respond(500, json=response_body)
    rsp2 = httpx2_mock.get(url, params=query).respond(500, json=response_body)
    rsp3 = httpx2_mock.get(url, params=query).respond(500, json=response_body)
    rsp4 = httpx2_mock.get(url, params=query).respond(200, json={"success": "true"})

    response = AlmaClient().get_barcode("some_barcode")
    assert rsp1.call_count == 1
    assert rsp2.call_count == 1
    assert rsp3.call_count == 1
    assert rsp4.call_count == 1
    assert response == {"success": "true"}


def test_get_barcode_handles_other_error(httpx2_mock):
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    response_body = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<web_service_result xmlns="http://com/exlibris/urm/general/xmlbeans">
            <errorsExist>true</errorsExist>
            <errorList>
                        <error>
                                    <errorCode>UNAUTHORIZED</errorCode>
                                    <errorMessage>API-key not defined or not configured to allow this API.</errorMessage>
                        </error>
    </errorList>
</web_service_result>
    """

    httpx2_mock.get(url, params=query).respond(400, text=response_body)
    with pytest.raises(Exception) as exc_info:
        AlmaClient().get_barcode("some_barcode")
    assert exc_info.type is HTTPStatusError
