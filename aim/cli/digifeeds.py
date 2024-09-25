import typer
from aim.digifeeds.database import models, main

app = typer.Typer()


@app.command()
def add_to_db(barcode: str):
    print(f'Adding barcode "{barcode}" to database')


@app.command()
def load_statuses():
    with main.SessionLocal() as db_session:
        models.load_statuses(session=db_session)
