from aim.digifeeds.alma_client import AlmaClient
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import Item
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
            else:
                raise ext_inst
        item = Item(
            DBClient().add_item_status(barcode=barcode, status="added_to_digifeeds_set")
        )
    return item
