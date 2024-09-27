import typer
from aim.digifeeds.add_to_db import add_to_db as add_to_digifeeds_db
from aim.digifeeds.list_barcodes_in_bucket import list_barcodes_in_bucket
from aim.digifeeds.database import models, main


app = typer.Typer()


@app.command()
def add_to_db(barcode: str):
    add_to_digifeeds_db(barcode)
    print(f'Adding barcode "{barcode}" to database')


@app.command()
def load_statuses():
    with main.SessionLocal() as db_session:
        models.load_statuses(session=db_session)


@app.command()
def list_barcodes_in_input_bucket():
    print(list_barcodes_in_bucket(), end="")
