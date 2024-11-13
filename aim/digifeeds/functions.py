from aim.services import S
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import Item
import requests
import boto3
from pathlib import Path


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
