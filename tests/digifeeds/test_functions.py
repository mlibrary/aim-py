import json
from aim.digifeeds.functions import (
    rclone,
    barcodes_added_in_last_two_weeks,
    write_barcodes_added_in_last_two_weeks_report,
    generate_barcodes_added_in_last_two_weeks_report,
)
from io import StringIO


def test_barcodes_added_in_last_two_weeks(mocker):
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
    output = barcodes_added_in_last_two_weeks()
    assert output == [
        ["2024-12-14", "35112203951670"],
        ["2024-12-14", "39015004707009"],
    ]


def test_write_barcodes_added_in_last_two_weeks_report(mocker):
    outfile = StringIO()
    barcodes = [
        ["2024-12-14", "35112203951670"],
        ["2024-12-14", "39015004707009"],
    ]

    mocker.patch(
        "aim.digifeeds.functions.barcodes_added_in_last_two_weeks",
        return_value=barcodes,
    )
    write_barcodes_added_in_last_two_weeks_report(outfile)
    outfile.seek(0)
    content = outfile.read()
    assert content == "2024-12-14\t35112203951670\n2024-12-14\t39015004707009\n"


def test_generate_barcodes_added_in_last_two_weeks_report(mocker):
    rclone_mock = mocker.patch.object(rclone, "copyto")
    report_writer_mock = mocker.patch(
        "aim.digifeeds.functions.write_barcodes_added_in_last_two_weeks_report",
    )

    generate_barcodes_added_in_last_two_weeks_report()
    rclone_mock.assert_called()
    report_writer_mock.assert_called()
