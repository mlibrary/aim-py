"""Main AIM CLI
===============

This hooks up the AIM CLI application. Nothing exciting happening here.
"""

import typer
from aim.services import S


def should_load(app_name: str):
    return S.app_name == "aim" or S.app_name == app_name


app = typer.Typer()
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


if __name__ == "__main__":  # pragma: no cover
    app()
