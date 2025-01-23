from typer.testing import CliRunner
from aim.cli.main import app
from aim.hathifiles import poll

runner = CliRunner()


def test_hathifiles_create_store_file(mocker):
    create_store_file_mock = mocker.patch.object(poll, "create_store_file")

    result = runner.invoke(app, ["hathifiles", "create-store-file"])

    assert result.exit_code == 0
    assert create_store_file_mock.call_count == 1


def test_hathifiles_check_for_new_update_files(mocker):
    create_files_mock = mocker.patch.object(poll, "check_for_new_update_files")

    result = runner.invoke(app, ["hathifiles", "check-for-new-update-files"])

    assert result.exit_code == 0
    assert create_files_mock.call_count == 1
