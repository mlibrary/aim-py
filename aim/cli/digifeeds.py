"""Digifeeds CLI
====================
"""

import typer
from typing_extensions import Annotated, Literal
from typing import List
from aim.digifeeds.database import models, main
from aim.digifeeds import functions
from aim.digifeeds.item import get_item, process_item
from aim.services import S

import json
import sys


app = typer.Typer()


@app.command()
def add_to_digifeeds_set(
    barcode: Annotated[
        str,
        typer.Argument(help="The barcode to be added to the database"),
    ],
):
    """
    Add a barcode to the *Digifeeds Database* and then to the Alma Digifeeds Set

    If the barcode is in the database fetch it and then try to add it to the
    Digifeeds set in Alma. Prints an error message if the barcode isn't found in Alma.
    Prints the status of adding the item to the digifeeds set.

    Args:
        barcode (str): Barcode of item
    """
    S.logger.info(
        "add_to_digifeeds_set_start",
        message="Start adding item to digifeeds set",
        barcode=barcode,
    )
    item = get_item(barcode)
    result = item.add_to_digifeeds_set()

    if result.has_status("not_found_in_alma"):
        S.logger.info(
            "not_found_in_alma", message="Item not found in alma.", barcode=barcode
        )

    if result.has_status("added_to_digifeeds_set"):
        S.logger.info(
            "added_to_digifeeds_set",
            message="Item added to digifeeds set",
            barcode=barcode,
        )
    else:
        S.logger.error(
            "not_added_to_digifeeds_set",
            message="Item NOT added to digifeeds set",
            barcode=barcode,
        )


@app.command()
def check_zephir(
    barcode: Annotated[
        str,
        typer.Argument(
            help="The barcode to check in zephir. It should NOT have mdp prefix. The barcode must already exist in the digifeeds database."
        ),
    ],
):
    """
    Check if barcode has metadata in Zephir
    """

    print(f"Checking Zephir for {barcode}")
    item = get_item(barcode)
    result = item.check_zephir()
    if result:
        S.logger.info("in_zephir", message="Item is in zephir", barcode=barcode)
    else:
        S.logger.info("not_in_zephir", message="Item is NOT in zephir", barcode=barcode)


@app.command()
def load_statuses():
    """
    Load the statuses into the database.
    """
    with main.SessionLocal() as db_session:
        models.load_statuses(session=db_session)


@app.command()
def list_barcodes_in_input_bucket():
    """
    List the barcodes currently in the input directory in the S3 bucket.
    """
    json.dump(functions.list_barcodes_in_input_bucket(), sys.stdout)


@app.command()
def list_barcodes_potentially_in_hathifiles():
    """
    List the barcodes of items that have gone through the digifeeds process and
    could be in hathitrust. These are items with status `pending_deletion` and
    without status `in_hathifiles`.
    """
    json.dump(functions.list_barcodes_potentially_in_hathifiles(), sys.stdout)


@app.command()
def move_to_pickup(
    barcode: Annotated[
        str,
        typer.Argument(help="The barcode to be added to the database"),
    ],
):
    """
    Moves the zipped volume from the s3 bucket to the pickup location for
    google. When it's finished, the volume is moved to the processed folder in
    the bucket and prefixed with the date and time.
    """
    S.logger.info(
        "move_to_pickup_start",
        message="Start moving item from s3 bucket to google pickup location",
        barcode=barcode,
    )
    item = get_item(barcode)
    result = item.move_to_pickup()
    if result is None:
        S.logger.info(
            "not_in_zephir_long_enough",
            message="Item has not been in zephir long enough",
            barcode=barcode,
        )
    else:
        S.logger.info(
            "move_to_pickup_success",
            message="Item has been successfully moved to pickup",
            barcode=barcode,
        )


@app.command()
def process_barcode(
    barcode: Annotated[
        str,
        typer.Argument(help="The barcode to run the digifeeds process on"),
    ],
):
    """
    Runs through the whole process for a barcode: adding it to the digifeeds set,
    checking zephir, and moving the item to the pickup google drive.
    """

    item = get_item(barcode)
    process_item(item)


@app.command()
def process_barcodes(
    barcodes: Annotated[
        List[str],
        typer.Argument(help="The list of barcodes to run the digifeeds process on"),
    ],
):
    """
    Runs through the whole process for each of the given barcodes: adding it to
    the digifeeds set, checking zephir, and moving the item to the pickup google
    drive.
    """
    for barcode in barcodes:
        item = get_item(barcode)
        process_item(item)


@app.command()
def check_and_update_hathifiles_timestamp(
    barcodes: Annotated[
        List[str],
        typer.Argument(help="The list of barcodes to check and update"),
    ],
):
    for barcode in barcodes:
        item = get_item(barcode)
        item.check_and_update_hathifiles_timestamp()


@app.command()
def generate_barcodes_in_s3_report():
    """
    Generates a report of barcodes that have been moved to the google pickup
    location in the last two weeks. It is based on the files in the processed
    location in the s3 bucket. This report is sent to a folder on Mayhem.
    """
    functions.generate_barcodes_added_in_last_two_weeks_report()


@app.command()
def generate_barcodes_in_hathifiles_report():
    """
    Generates a report of barcodes that have been found in the Hathifiles
    Database in the last two weeks. The dates in the report are the
    rights-timestamp in the Hathifiles.
    """
    functions.generate_barcodes_in_hathifiles_report()


@app.command()
def prune(
    location: Annotated[
        Literal["s3", "filesystem"],
        typer.Argument(help="The location from which to prune barcodes"),
    ],
):
    """
    Deletes zips and folders of images in paths of images that have been newly
    sent through digifeeds and have now been found in the hathifiles. The
    filesystem is Mayhem.
    """
    rclone_mapping = {
        "s3": f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_prunable_path}",
        "filesystem": f"{S.digifeeds_fileserver_rclone_remote}:{S.digifeeds_fileserver_prunable_path}",
    }
    functions.prune_processed_barcodes(rclone_path=rclone_mapping[location])
