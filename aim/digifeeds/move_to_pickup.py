from rclone_python import rclone
from aim.digifeeds.item import Item
from aim.digifeeds.db_client import DBClient
from aim.services import S
from datetime import datetime

print(rclone.is_installed())


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
