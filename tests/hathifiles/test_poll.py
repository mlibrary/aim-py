import pytest
import json
import responses
from aim.hathifiles.poll import get_hathi_file_list, filter_for_update_files, get_store


@pytest.fixture
def file_list_data():
    with open("tests/fixtures/hathifiles/poll/hathi_file_list.json") as f:
        output = json.load(f)
    return output


def test_filter_for_update_files(file_list_data):
    hfl = filter_for_update_files(file_list_data)
    assert hfl == ["hathi_upd_20241113.txt.gz", "hathi_upd_20241114.txt.gz"]


@responses.activate
def test_get_hathi_file_list(file_list_data):
    url = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
    responses.get(url, json=file_list_data, status=200)
    hfl = get_hathi_file_list()
    assert hfl == file_list_data


def test_get_store_returns_store_when_valid_file_exists():
    store = get_store("tests/fixtures/hathifiles/poll/hathi_file_list_store.json")
    assert "file1" in store
    assert "file2" in store
    assert "not_in_store" not in "store"


def test_get_store_errors_out_when_file_not_found():
    with pytest.raises(Exception) as exc_info:
        get_store("this_file_does_not_exist.txt")
    assert exc_info.type is FileNotFoundError
