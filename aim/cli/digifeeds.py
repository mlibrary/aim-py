"""Digifeeds CLI
====================
"""

import typer
from typing_extensions import Annotated
from aim.digifeeds.add_to_db import add_to_db as add_to_digifeeds_db
from aim.digifeeds.list_barcodes_in_bucket import list_barcodes_in_bucket

# from aim.digifeeds.check_zephir import check_zephir as check_zephir_for_barcode
from aim.digifeeds.move_to_pickup import move_to_pickup as move_volume_to_pickup
from aim.digifeeds.database import models, main
from aim.digifeeds import functions

import json
import sys


app = typer.Typer()


@app.command()
def add_to_db(
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
    print(f'Adding barcode "{barcode}" to database')
    item = add_to_digifeeds_db(barcode)
    if item.has_status("not_found_in_alma"):
        print("Item not found in alma.")
    if item.has_status("added_to_digifeeds_set"):
        print("Item added to digifeeds set")
    else:
        print("Item NOT added to digifeeds set")


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
        print(f"{barcode} is in Zephir")
    else:
        print(f"{barcode} is NOT in Zephir")


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
    json.dump(list_barcodes_in_bucket(), sys.stdout)


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
    print(f'Moving barcode "{barcode}" from the s3 bucket to the google drive')
    item = move_volume_to_pickup(barcode)
    if item is None:
        print("Item has not been in zephir long enough")
    else:
        print("Item has been successfully moved to pickup")
