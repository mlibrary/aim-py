from aim.digifeeds.database import crud
from aim.digifeeds.database.schemas import ItemCreate
import pytest


@pytest.fixture()
def valid_item(db_session):
    return crud.add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))


@pytest.fixture()
def valid_in_zephir_item(db_session):
    item = crud.add_item(db=db_session, item=ItemCreate(barcode="in_zephir_item"))
    status = crud.get_status(db=db_session, name="in_zephir")
    crud.add_item_status(db=db_session, item=item, status=status)
    db_session.refresh(item)
    return item


def test_get_statuses(client):
    response = client.get("/statuses")
    assert response.status_code == 200, response.text


def test_get_items(client, valid_item, valid_in_zephir_item):
    valid_item
    valid_in_zephir_item
    response = client.get("/items")
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 2


def test_get_items_with_in_zephir_true(client, valid_item, valid_in_zephir_item):
    valid_item
    valid_in_zephir_item
    response = client.get("/items", params={"filter": "in_zephir"})
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["barcode"] == valid_in_zephir_item.barcode


def test_get_items_with_in_zephir_false(client, valid_item, valid_in_zephir_item):
    valid_item
    valid_in_zephir_item
    response = client.get("/items", params={"filter": "not_in_zephir"})
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["barcode"] == valid_item.barcode


def test_get_item(client, valid_item, valid_in_zephir_item):
    valid_item
    valid_in_zephir_item
    response = client.get(f"/items/{valid_item.barcode}")
    assert response.status_code == 200, response.text


def test_get_item_not_found(client):
    response = client.get("/items/some_barcode_that_does_not_exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_create_item(client):
    response = client.post("items/new_barcode")
    assert response.status_code == 200, response.text


def test_create_existing_item(client, valid_item):
    response = client.post(f"items/{valid_item.barcode}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Item already exists"}


def test_update_item_success(client, valid_item):
    response = client.put(f"items/{valid_item.barcode}/status/in_zephir")
    assert response.status_code == 200, response.text


def test_update_nonexisting_item(client):
    response = client.put("/items/some_barcode_that_does_not_exist/status/in_zephir")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_update_existing_item_with_nonexistent_status(client, valid_item):
    response = client.put(f"/items/{valid_item.barcode}/status/non_existent_status")
    assert response.status_code == 404
    assert response.json() == {"detail": "Status not found"}


def test_update_item_with_hathifiles_timestamp(client, valid_item):
    timestamp = "2012-09-13T18:30:03"
    response = client.put(
        f"/items/{valid_item.barcode}/hathifiles_timestamp/{timestamp}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["hathifiles_timestamp"] == timestamp


def test_update_item_with_nonexistent_barcode(client):
    timestamp = "2012-09-13T18:30:03"
    response = client.put(
        f"/items/some_barcode_that_does_not_exist/hathifiles_timestamp/{timestamp}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_update_item_with_invalid_timestamp(client, valid_item):
    response = client.put(
        f"/items/{valid_item.barcode}/hathifiles_timestamp/not_an_iso_date_string"
    )
    assert response.status_code == 422


def test_update_item_that_is_already_is_in_hf(client, valid_item):
    timestamp = "2012-09-13T18:30:03"
    client.put(f"/items/{valid_item.barcode}/hathifiles_timestamp/{timestamp}")
    response = client.put(
        f"/items/{valid_item.barcode}/hathifiles_timestamp/{timestamp}"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Item already has a hathifiles_timestamp"}


def test_delete_item(client, valid_item):
    response = client.delete(f"/items/{valid_item.barcode}")
    assert response.status_code == 200, response.text


def test_delete_not_existent_item(client):
    response = client.delete("/items/barcode_does_not_exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}
