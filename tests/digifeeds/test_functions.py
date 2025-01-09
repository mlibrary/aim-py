import json
from aim.digifeeds.functions import rclone, barcodes_added_in_last_two_weeks


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