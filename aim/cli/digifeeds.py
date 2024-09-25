import typer

app = typer.Typer()


@app.command()
def add_to_db(barcode: str):
    print(f'Adding barcode "{barcode}" to database')
