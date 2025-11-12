import pytest
from rclone_python import rclone
import responses
import json
from aim.services import S
from aim.digifeeds.functions import prune_processed_barcodes


@pytest.fixture
def test_dir(tmp_path):
    rclone_config_path = tmp_path / "rclone.conf"
    test_path = tmp_path / "test"
    test_path.mkdir()
    rclone_config_path.write_text(
        f"""
[test_filesystem]
type = alias
remote = {test_path} 
""",
        encoding="utf-8",
    )
    rclone.set_config_file(config_file=rclone_config_path)
    yield test_path


@pytest.fixture
def item():
    with open("tests/fixtures/digifeeds/item.json") as f:
        output = json.load(f)
    return output


@pytest.fixture
def item_in_hathifiles(item):
    def _item_in_hathifiles(barcode):
        result = item.copy()
        result["barcode"] = barcode
        result["hathifiles_timestamp"] = "2024-12-14T02:01:05"
        result["statuses"].append(
            {
                "name": "in_hathifiles",
                "description": "Barcode was found in the Hathifiles Database",
                "created_at": "2024-09-25T17:13:28",
            }
        )
        return result

    return _item_in_hathifiles


@responses.activate
def test_prune_processed_barcodes_deletes_items_in(test_dir, item_in_hathifiles):
    (test_dir / "2025-10-11_02-30-02_39barcode1.zip").touch()
    (test_dir / "2025-10-11_02-30-02_39barcode1").mkdir()
    (test_dir / "2025-10-11_02-30-02_39barcode1" / "some_image.jpg").touch()

    barcode1 = item_in_hathifiles("39barcode1")
    responses.get(f"{S.digifeeds_api_url}/items/39barcode1", json=barcode1)

    prune_processed_barcodes(rclone_path="test_filesystem:")
    assert len(list(test_dir.iterdir())) == 0


@responses.activate
def test_prune_processed_barcodes_leaves_items_not_in_hathi_trust(test_dir, item):
    (test_dir / "2025-10-11_02-30-02_39barcode1.zip").touch()
    (test_dir / "2025-10-11_02-30-02_39barcode1").mkdir()
    (test_dir / "2025-10-11_02-30-02_39barcode1" / "some_image.jpg").touch()

    item["barcode"] = "39barcode1"
    responses.get(f"{S.digifeeds_api_url}/items/39barcode1", json=item)
    prune_processed_barcodes(rclone_path="test_filesystem:")
    assert len(list(test_dir.iterdir())) == 2
