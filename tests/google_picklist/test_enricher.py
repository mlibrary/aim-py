import pytest
import json
from aim.services import S
import responses
from responses import matchers
from aim.google_picklist.enricher import AlmaItem, main


@pytest.fixture
def item_data():
    with open("tests/fixtures/google_picklist/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def item2_data():
    with open("tests/fixtures/google_picklist/item2.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def picklist():
    with open("tests/fixtures/google_picklist/picklist.txt") as f:
        return f.read()


@responses.activate
def test_main(tmp_path, tmpdir, picklist, item2_data):

    url = f"{S.alma_api_url}/items"
    not_found_body = {
        "errorsExist": True,
        "errorList": {
            "error": [
                {
                    "errorCode": "401689",
                    "errorMessage": "No items found for barcode B29446.",
                    "trackingId": "E01-2507134129-Z0415-AWAE2086938389",
                }
            ]
        },
    }
    responses.get(
        url,
        match=[
            matchers.query_param_matcher({"item_barcode": "39015005144582"}),
        ],
        json=item2_data,
        status=200,
    )
    responses.get(
        url,
        match=[
            matchers.query_param_matcher({"item_barcode": "B29446"}),
        ],
        json=not_found_body,
        status=400,
    )

    input_file = tmp_path / "input.txt"
    input_file.write_text(picklist, encoding="utf-8")
    output_file = tmpdir.join("output.txt")
    main(input_path=input_file, output_path=output_file)

    expected = """990000961520106381\tBriefe, 1913-1959 /\tHATCH\tGRAD\t39015005144582\t\tN6888.G88 A35\t\t\tItem not in place\t
barcode not found: B29446\n"""

    assert (output_file.read()) == expected


def test_alma_item_row(item_data):
    subject = AlmaItem(item_data).row()
    assert (
        subject
        == "990040063470106381\tOpera musica /\tMUSIC\tMAIN\t39015040218748\tmdp.39015040218748\tM 3 .P52 1993\t\t\tItem in place\t\n"
    )


def test_alma_item_htid(item_data):
    assert (AlmaItem(item_data).htid) == "mdp.39015040218748"


def test_alma_item_missing_htid(item_data):
    del item_data["item_data"]["alternative_call_number"]
    assert (AlmaItem(item_data).htid) == ""
