"""Digifeeds CLI
====================
"""

import typer
from typing_extensions import Annotated
from aim.digifeeds.database import models, main
from aim.digifeeds import functions
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
    item = functions.add_to_digifeeds_set(barcode)
    if item.has_status("not_found_in_alma"):
        S.logger.info(
            "not_found_in_alma", message="Item not found in alma.", barcode=barcode
        )
    if item.has_status("added_to_digifeeds_set"):
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
    item = functions.check_zephir(barcode)
    if item:
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
def move_to_pickup(
    barcode: Annotated[
        str,
        typer.Argument(help="The barcode to be added to the database"),
    ],
):
    """
    Moves the zipped volume from the s3 bucket to the google drive folder for
    pickup from google. When it's finished, the volume is moved to the processed
    folder in the bucket and prefixed with the date and time.
    """
    S.logger.info(
        "move_to_pickup_start",
        message="Start moving item from s3 bucket to pickup google drive",
        barcode=barcode,
    )
    item = functions.move_to_pickup(barcode)
    if item is None:
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
