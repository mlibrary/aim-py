from datetime import datetime, date, timedelta
import json
from aim.digifeeds.functions import (
    rclone,
    barcodes_added_in_last_two_weeks,
    write_and_send_report_to_mayhem,
    generate_barcodes_added_in_last_two_weeks_report,
    generate_barcodes_in_hathifiles_report,
    last_two_weeks_rclone_filter,
    list_barcodes_in_input_bucket,
    list_barcodes_potentially_in_hathifiles,
    barcodes_in_hathifiles_in_last_two_weeks,
    barcode_from_name,
)
from aim.services import S
import responses
import pytest
from responses import matchers
import tempfile


@pytest.fixture
def item_list():
    with open("tests/fixtures/digifeeds/item_list.json") as f:
        output = json.load(f)
    return output


def test_list_barcodes_in_input_bucket(mocker):
    ls_data_raw = """
    [
      {
        "Path": "35112203951670.zip",
        "Name": "35112203951670.zip",
        "Size": 554562627,
        "MimeType": "application/zip",
        "ModTime": "2024-12-14T02:01:05.093051502-05:00",
        "IsDir": false,
        "Tier": "STANDARD"
      },
      {
        "Path": "39015004707009.zip",
        "Name": "39015004707009.zip",
        "Size": 232895588,
        "MimeType": "application/zip",
        "ModTime": "2024-12-14T02:02:29.111076546-05:00",
        "IsDir": false,
        "Tier": "STANDARD"
      }
    ]
"""
    mocker.patch.object(rclone, "ls", return_value=json.loads(ls_data_raw))
    subject = list_barcodes_in_input_bucket()

    assert subject == ["35112203951670", "39015004707009"]


@responses.activate
def test_list_barcodes_potentially_in_hathifiles(item_list):
    item_list["total"] = 1
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        match=[
            matchers.query_param_matcher(
                {
                    "limit": 50,
                    "offset": 0,
                    "q": "status:pending_deletion -status:in_hathifiles",
                }
            )
        ],
        json=item_list,
    )

    subject = list_barcodes_potentially_in_hathifiles()
    assert subject == ["some_barcode"]


def test_last_two_weeks_rclone_filter():
    filters = last_two_weeks_rclone_filter(
        start_date=datetime.strptime("2025-01-02", "%Y-%m-%d")
    )
    expected_filter_string = (
        "{2025-01-02*,2025-01-01*,2024-12-31*,2024-12-30*,2024-12-29*"
        ",2024-12-28*,2024-12-27*,2024-12-26*,2024-12-25*,2024-12-24*"
        ",2024-12-23*,2024-12-22*,2024-12-21*,2024-12-20*}"
    )
    assert filters == expected_filter_string


def test_barcodes_added_in_last_two_weeks(mocker):
    ls_data_raw = """
    [
      {
        "Path": "2024-12-01_07-10-02_35112203951670.zip",
        "Name": "2024-12-01_07-10-02_35112203951670.zip",
        "Size": 554562627,
        "MimeType": "application/zip",
        "ModTime": "2024-12-14T02:01:05.093051502-05:00",
        "IsDir": false,
        "Tier": "STANDARD"
      },
      {
        "Path": "2024-12-01_07-10-02_39015004707009.zip",
        "Name": "2024-12-01_07-10-02_39015004707009.zip",
        "Size": 232895588,
        "MimeType": "application/zip",
        "ModTime": "2024-12-14T02:02:29.111076546-05:00",
        "IsDir": false,
        "Tier": "STANDARD"
      }
    ]
"""
    mocker.patch.object(rclone, "ls", return_value=json.loads(ls_data_raw))
    output = barcodes_added_in_last_two_weeks()
    assert output == [
        ["12/01/2024", "35112203951670"],
        ["12/01/2024", "39015004707009"],
    ]


def test_generate_barcodes_added_in_last_two_weeks_report(mocker):
    barcode_list_mock = mocker.patch(
        "aim.digifeeds.functions.barcodes_added_in_last_two_weeks",
    )
    write_and_send_mock = mocker.patch(
        "aim.digifeeds.functions.write_and_send_report_to_mayhem",
    )

    generate_barcodes_added_in_last_two_weeks_report()

    write_and_send_mock.assert_called()
    barcode_list_mock.assert_called()


def test_generate_barcodes_in_hathitrust_report(mocker):
    barcode_list_mock = mocker.patch(
        "aim.digifeeds.functions.barcodes_in_hathifiles_in_last_two_weeks",
    )
    write_and_send_mock = mocker.patch(
        "aim.digifeeds.functions.write_and_send_report_to_mayhem",
    )

    generate_barcodes_in_hathifiles_report()

    write_and_send_mock.assert_called()
    barcode_list_mock.assert_called()


def test_write_and_send_report_to_mayhem(mocker):
    rclone_mock = mocker.patch.object(rclone, "copyto")
    content = [
        ["12/14/2024", "35112203951670"],
        ["12/14/2024", "39015004707009"],
    ]
    tf = tempfile.NamedTemporaryFile(mode="w+t")

    write_and_send_report_to_mayhem(
        content=content,
        base_name="my_cool_report",
        rclone_path="my_mayhem_remote:",
        report_file=tf,
    )

    rclone_mock.assert_called()
    assert tf.read() == "12/14/2024\t35112203951670\n12/14/2024\t39015004707009\n"


@responses.activate
def test_barcodes_in_hathifiles_in_last_two_weeks(item_list):
    item_list["total"] = 1
    item_list["items"][0]["hathifiles_timestamp"] = "2009-03-02 22:30:12"
    two_weeks_ago = date.today() - timedelta(14)
    url = f"{S.digifeeds_api_url}/items"
    responses.get(
        url=url,
        match=[
            matchers.query_param_matcher(
                {
                    "limit": 50,
                    "offset": 0,
                    "q": f"status.in_hathifiles.created_at>={two_weeks_ago.isoformat()}",
                }
            )
        ],
        json=item_list,
    )

    subject = barcodes_in_hathifiles_in_last_two_weeks()
    assert subject == [
        [
            "some_barcode",
            "03/02/2009",
            "https://babel.hathitrust.org/cgi/pt?id=mdp.some_barcode",
        ]
    ]


def test_barcode_from_name_handles_directory_style_name():
    assert (barcode_from_name("2025-10-11_02-30-02_39barcode1")) == "39barcode1"


def test_barcode_from_name_handles_zip():
    assert (barcode_from_name("2025-10-11_02-30-02_39barcode1.zip")) == "39barcode1"
