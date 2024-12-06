from aim.services import S
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import Item
import requests
import boto3
from pathlib import Path
from rclone_python import rclone
from datetime import datetime
from aim.digifeeds.alma_client import AlmaClient
from requests.exceptions import HTTPError


def move_to_pickup(barcode: str):
    item = Item(DBClient().get_or_add_item(barcode))

    if not item.in_zephir_for_long_enough:
        return None

    DBClient().add_item_status(barcode=barcode, status="copying_start")
    rclone.copyto(
        f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}/{barcode}.zip",
        f"{S.digifeeds_gdrive_rclone_remote}:{barcode}.zip",
    )
    DBClient().add_item_status(barcode=barcode, status="copying_end")
    timestamp = datetime.now().strftime("%F_%H-%M-%S")
    rclone.moveto(
        f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}/{barcode}.zip",
        f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_processed_path}/{timestamp}_{barcode}.zip",
    )
    final_raw_item = DBClient().add_item_status(
        barcode=barcode, status="pending_deletion"
    )

    return final_raw_item


def list_barcodes_in_input_bucket():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S.digifeeds_s3_access_key,
        aws_secret_access_key=S.digifeeds_s3_secret_access_key,
    )
    prefix = S.digifeeds_s3_input_path + "/"
    response = s3.list_objects_v2(Bucket=S.digifeeds_s3_bucket, Prefix=prefix)
    barcodes = [Path(object["Key"]).stem for object in response["Contents"]]
    return barcodes
