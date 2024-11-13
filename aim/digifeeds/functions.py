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


def add_to_db(barcode: str):
    """Add a barcode to the digifeeds database

    Args:
        barcode (str): Barcode of the item

    Raises:
        ext_inst: HTTPError

    Returns:
        aim.digifeeds.database.models.Item: Item object
    """
    item = Item(DBClient().get_or_add_item(barcode))
    if not item.has_status("added_to_digifeeds_set"):
        try:
            AlmaClient().add_barcode_to_digifeeds_set(barcode)
        except HTTPError as ext_inst:
            errorList = ext_inst.response.json()["errorList"]["error"]
            if any(e["errorCode"] == "60120" for e in errorList):
                if not item.has_status("not_found_in_alma"):
                    item = Item(
                        DBClient().add_item_status(
                            barcode=barcode, status="not_found_in_alma"
                        )
                    )
                return item
            elif any(e["errorCode"] == "60115" for e in errorList):
                # 60115 means the barcode is already in the set. That means the
                # db entry from this barcdoe needs to have
                # added_to_digifeeds_set
                pass
            else:
                raise ext_inst
        item = Item(
            DBClient().add_item_status(barcode=barcode, status="added_to_digifeeds_set")
        )
    return item


def move_to_pickup(barcode: str):
    raw_item = DBClient().get_item(barcode)
    if raw_item is None:
        raise Exception("Item not found in database")

    item = Item(raw_item)

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


def check_zephir(barcode: str):
    raw_item = DBClient().get_item(barcode)
    if raw_item is None:
        raise Exception("Item not found in database")

    item = Item(raw_item)

    if item.has_status("in_zephir"):
        return item

    response = requests.get(f"{S.zephir_bib_api_url}/mdp.{barcode}")
    if response.status_code == 200:
        DBClient().add_item_status(barcode=barcode, status="in_zephir")
        return item
    else:
        return None
