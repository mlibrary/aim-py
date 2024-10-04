import typer
from aim.digifeeds.add_to_db import add_to_db as add_to_digifeeds_db
from aim.digifeeds.list_barcodes_in_bucket import list_barcodes_in_bucket
from aim.digifeeds.database import models, main
import json
import sys


app = typer.Typer()


@app.command()
def add_to_db(barcode: str):
    print(f'Adding barcode "{barcode}" to database')
    item = add_to_digifeeds_db(barcode)
    if item.has_status("not_found_in_alma"):
        print("Item not found in alma.")
    if item.has_status("added_to_digifeeds_set"):
        print("Item added to digifeeds set")
    else:
        print("Item not added to digifeeds set")


@app.command()
def load_statuses():
    with main.SessionLocal() as db_session:
        models.load_statuses(session=db_session)


@app.command()
def list_barcodes_in_input_bucket():
    json.dump(list_barcodes_in_bucket(), sys.stdout)
