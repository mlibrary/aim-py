import pytest
import json
import responses
from responses import matchers
import os
from requests.exceptions import HTTPError
from structlog.testing import capture_logs
from aim.services import S
from aim.hathifiles.poll import (
    get_latest_update_files,
    get_store,
    create_store_file,
    check_for_new_files,
    NewFileHandler,
)


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


# Clean up: Remove the temporary files after the tests
@pytest.fixture(autouse=True)
def cleanup_temp_files(temp_dir):
    yield
    for file in temp_dir.iterdir():
        if file.is_file():
            os.remove(file)


@pytest.fixture
def file_list_data():
    with open("tests/fixtures/hathifiles/poll/hathi_file_list.json") as f:
        output = json.load(f)
    return output


@responses.activate
def test_get_latest_update_files(file_list_data):
    url = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    responses.get(url, json=file_list_data, status=200)
    hfl = get_latest_update_files()
    assert hfl == ["hathi_upd_20241113.txt.gz", "hathi_upd_20241114.txt.gz"]


@responses.activate
def test_get_latest_update_files_fetch_fail(file_list_data):
    url = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    responses.get(url, json=file_list_data, status=500)
    with pytest.raises(Exception) as exc_info:
        get_latest_update_files()
    assert exc_info.type is HTTPError


def test_get_store_returns_store_when_valid_file_exists():
    store = get_store("tests/fixtures/hathifiles/poll/hathi_file_list_store.json")
    assert "file1" in store
    assert "file2" in store
    assert "not_in_store" not in "store"


def test_get_store_errors_out_when_file_not_found():
    with pytest.raises(Exception) as exc_info:
        get_store("this_file_does_not_exist.txt")
    assert exc_info.type is FileNotFoundError


class FakeNewFileHandler(NewFileHandler):
    def notify_webhook(self):
        S.logger.info("Notify webhook")

    def replace_store(self):
        S.logger.info("Replace store")


def test_check_for_new_files_when_no_new_files():
    with capture_logs() as cap_logs:
        check_for_new_files(
            latest_update_files=["file1"],
            store=["other_file", "file1"],
            new_file_handler_klass=FakeNewFileHandler,
        )
        assert any(log["event"] == "No new Hathifiles update files" for log in cap_logs)


def test_check_for_new_files_when_there_are_new_files():
    with capture_logs() as cap_logs:
        check_for_new_files(
            latest_update_files=["file1", "file2", "file3"],
            store=["other_file", "file1"],
            new_file_handler_klass=FakeNewFileHandler,
        )
        assert any(log["event"] == "New Hathifiles update file(s)" for log in cap_logs)
        assert any(log["file_names"] == "file2,file3" for log in cap_logs)
        assert any(log["event"] == "Notify webhook" for log in cap_logs)
        assert any(log["event"] == "Replace store" for log in cap_logs)


@responses.activate
def test_create_store_file_when_file_does_not_exist(file_list_data, temp_dir):
    url = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    responses.get(url, json=file_list_data, status=200)
    store_path = temp_dir / "test_store_file.json"
    create_store_file(store_path)
    with open(store_path, "r") as f:
        file_contents = json.load(f)

    assert file_contents == ["hathi_upd_20241113.txt.gz", "hathi_upd_20241114.txt.gz"]


def test_create_store_file_when_file_exists(temp_dir):
    store_path = temp_dir / "test_store_file.json"
    with open(store_path, "w") as f:
        f.write("This_is_a_line")

    with capture_logs() as cap_logs:
        create_store_file(store_path)
        assert any(
            log["event"] == "HathiFiles store file already exists. Leaving alone."
            for log in cap_logs
        )


@responses.activate
def test_new_file_handler_notify_webhook_success():
    new_files = ["new_file"]
    webhook_stub = responses.post(
        S.hathifiles_webhook_url,
        match=[matchers.json_params_matcher({"file_names": new_files})],
        status=200,
    )
    handler = NewFileHandler(new_files=new_files, store="old_file")
    handler.notify_webhook()

    assert webhook_stub.call_count == 1


@responses.activate
def test_new_file_handler_notify_webhook_fail():
    new_files = ["new_file"]
    webhook_stub = responses.post(
        S.hathifiles_webhook_url,
        match=[matchers.json_params_matcher({"file_names": new_files})],
        status=500,
    )
    handler = NewFileHandler(new_files=new_files, store=["old_file"])

    with pytest.raises(Exception) as exc_info:
        handler.notify_webhook()

    assert exc_info.type is HTTPError
    assert webhook_stub.call_count == 1


def test_new_file_handler_replace_store(temp_dir):
    store_path = temp_dir / "test_store_file.json"
    with open(store_path, "w") as f:
        f.write("This_is_a_line")

    handler = NewFileHandler(new_files=["new_file"], store=["old_file"])

    handler.replace_store(store_path)

    with open(store_path, "r") as f:
        file_contents = json.load(f)

    assert file_contents == ["old_file", "new_file"]
