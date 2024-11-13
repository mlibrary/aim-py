from aim.services import S
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import Item
import requests


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
