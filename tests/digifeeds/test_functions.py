from datetime import datetime
import json
from aim.digifeeds.functions import (
    rclone,
    barcodes_added_in_last_two_weeks,
    write_barcodes_added_in_last_two_weeks_report,
    generate_barcodes_added_in_last_two_weeks_report,
    last_two_weeks_rclone_filter,
    list_barcodes_in_input_bucket,
)
from io import StringIO


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


def test_write_barcodes_added_in_last_two_weeks_report(mocker):
    outfile = StringIO()
    barcodes = [
        ["12/14/2024", "35112203951670"],
        ["12/14/2024", "39015004707009"],
    ]

    mocker.patch(
        "aim.digifeeds.functions.barcodes_added_in_last_two_weeks",
        return_value=barcodes,
    )
    write_barcodes_added_in_last_two_weeks_report(outfile)
    outfile.seek(0)
    content = outfile.read()
    assert content == "12/14/2024\t35112203951670\n12/14/2024\t39015004707009\n"


def test_generate_barcodes_added_in_last_two_weeks_report(mocker):
    rclone_mock = mocker.patch.object(rclone, "copyto")
    report_writer_mock = mocker.patch(
        "aim.digifeeds.functions.write_barcodes_added_in_last_two_weeks_report",
    )

    generate_barcodes_added_in_last_two_weeks_report()
    rclone_mock.assert_called()
    report_writer_mock.assert_called()
