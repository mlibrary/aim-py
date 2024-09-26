from aim.digifeeds.alma_client import AlmaClient
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import Item
from requests.exceptions import HTTPError


def add_to_db(barcode: str):
    item = Item(DBClient().get_or_add_item(barcode))
    if not item.has_status("added_to_digifeeds_set"):
        try:
            AlmaClient().add_barcode_to_digifeeds_set(barcode)
        except HTTPError as ext_inst:
            errorList = ext_inst.response.json()["errorList"]["error"]
            if any(e["errorCode"] == "60120" for e in errorList):
                DBClient().add_item_status(barcode=barcode, status="not_found_in_alma")
                return None
        DBClient().add_item_status(barcode=barcode, status="added_to_digifeeds_set")
