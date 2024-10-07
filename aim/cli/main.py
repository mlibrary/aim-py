import typer
import aim.cli.digifeeds as digifeeds

app = typer.Typer()
app.add_typer(
    digifeeds.app, name="digifeeds", help="Commands related to the digifeeds process"
)


if __name__ == "__main__":  # pragma: no cover
    app()
