from typer.testing import CliRunner
from aim.cli.main import app

runner = CliRunner()


def test_get_services():
    result = runner.invoke(app, ["get-services"])
    assert "logger" in result.stdout
