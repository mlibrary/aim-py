"""Main AIM CLI
===============

This hooks up the AIM CLI application. Nothing exciting happening here.
"""

import typer
from typing_extensions import Annotated
import json
from aim.services import S


def should_load(app_name: str):
    return S.app_name == "aim" or S.app_name == app_name


app = typer.Typer()


@app.command()
def get_services():
    """
    Show the keys and values of everything in the Services object
    """
    result = {}
    keys = S.__dict__.keys()
    for key in keys:
        result[key] = str(S.__dict__[key])
    print(json.dumps(result, indent=4))


if should_load("digifeeds"):
    import aim.cli.digifeeds as digifeeds

    app.add_typer(
        digifeeds.app,
        name="digifeeds",
        help="Commands related to the digifeeds process",
    )


if should_load("hathifiles"):
    import aim.cli.hathifiles as hathifiles

    app.add_typer(
        hathifiles.app,
        name="hathifiles",
        help="Commands related to the hathifiles database",
    )

if should_load("google_picklist"):
    from aim.google_picklist import enricher

    @app.command()
    def process_google_picklist(
        input_path: Annotated[
            str,
            typer.Option(
                "-i",
                help="The path to the input picklist file",
            ),
        ] = S.google_picklist_input_file_path,
        output_path: Annotated[
            str,
            typer.Option(
                "-o",
                help="The path to the enriched picklist file",
            ),
        ] = S.google_picklist_output_file_path,
    ):
        """
        Takes in a google picklist and adds extra info about each item from alma
        """
        enricher.main(input_path=input_path, output_path=output_path)


if __name__ == "__main__":  # pragma: no cover
    app()
