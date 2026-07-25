import responses
from responses import matchers

import pytest
from aim.services import S
from aim.google_picklist.alma_client import AlmaClient
from requests.exceptions import HTTPError


@responses.activate
def test_get_barcode_success():
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        json={"success": "true"},
        status=200,
    )
    response = AlmaClient().get_barcode("some_barcode")
    assert response == {"success": "true"}


@responses.activate
def test_get_barcode_not_found():
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
    responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        json=body,
        status=400,
        content_type="application/json",
    )
    response = AlmaClient().get_barcode("some_barcode")
    assert response == {"not_found": True}


@responses.activate
def test_get_barcode_retries_on_connection_problem():
    url = f"{S.alma_api_url}/items"
    query = {"item_barcode": "some_barcode"}
    response_body = "Error"
    rsp1 = responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        body=response_body,
        status=500,
    )
    rsp2 = responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        body=response_body,
        status=500,
    )
    rsp3 = responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        body=response_body,
        status=500,
    )
    rsp4 = responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        json={"success": "true"},
        status=200,
    )

    response = AlmaClient().get_barcode("some_barcode")
    assert rsp1.call_count == 1
    assert rsp2.call_count == 1
    assert rsp3.call_count == 1
    assert rsp4.call_count == 1
    assert response == {"success": "true"}


@responses.activate
def test_get_barcode_handles_other_error():
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

    responses.get(
        url,
        match=[
            matchers.query_param_matcher(query),
        ],
        body=response_body,
        status=400,
    )
    with pytest.raises(Exception) as exc_info:
        AlmaClient().get_barcode("some_barcode")
    assert exc_info.type is HTTPError
