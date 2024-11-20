from aim.digifeeds.database.crud import (
    get_item,
    get_items,
    add_item,
    get_status,
    get_statuses,
    add_item_status,
    get_items_total,
    delete_item,
    NotFoundError,
)
from aim.digifeeds.database import models
from sqlalchemy import select
from aim.digifeeds.database.schemas import ItemCreate
import pytest


class TestCrud:
    def test_get_item(self, db_session):
        item = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        barcode = item.barcode
        item_in_db = get_item(barcode=barcode, db=db_session)
        assert (item_in_db.barcode) == "valid_barcode"

    def test_get_item_that_does_not_exist(self, db_session):
        with pytest.raises(Exception) as exc_info:
            get_item(barcode="does not exist", db=db_session)
        assert exc_info.type is NotFoundError

    def test_get_items_and_total_any(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, filter=None, limit=2, offset=0)
        count = get_items_total(db=db_session, filter=None)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (items[0]) == item1
        assert (items[1]) == item2
        assert (count) == 2

    def test_get_items_and_total_in_zephir(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, filter="in_zephir", limit=2, offset=0)
        count = get_items_total(db=db_session, filter="in_zephir")
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1
        assert count == 1

    def test_get_items_and_total_not_in_zephir(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, filter="not_in_zephir", limit=2, offset=0)
        count = get_items_total(db=db_session, filter="not_in_zephir")
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item2
        assert count == 1

    def test_get_items_and_total_pending_deletion(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="pending_deletion")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, filter="pending_deletion", limit=2, offset=0)
        count = get_items_total(db=db_session, filter="pending_deletion")
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1
        assert count == 1

    def test_get_items_and_total_not_pending_deletion(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="pending_deletion")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(
            db=db_session, filter="not_pending_deletion", limit=2, offset=0
        )
        count = get_items_total(db=db_session, filter="pending_deletion")
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item2
        assert count == 1

    def test_get_items_and_total_not_found_in_alma(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="not_found_in_alma")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, filter="not_found_in_alma", limit=2, offset=0)
        count = get_items_total(db=db_session, filter="not_found_in_alma")
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1
        assert count == 1

    def test_get_status_that_exists(self, db_session):
        status = get_status(db=db_session, name="in_zephir")
        assert (status.name) == "in_zephir"

    def test_get_status_that_does_not_exist(self, db_session):
        with pytest.raises(Exception) as exc_info:
            get_status(name="does not exist", db=db_session)
        assert exc_info.type is NotFoundError

    def test_get_statuses(self, db_session):
        statuses = get_statuses(db=db_session)
        assert (len(statuses)) > 1
        assert (statuses[0].name) == "in_zephir"

    def test_delete_item(self, db_session):
        item = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item, status=status)
        delete_item(db=db_session, barcode=item.barcode)
        item_result = db_session.scalars(
            select(models.Item).filter_by(barcode=item.barcode)
        ).all()
        item_statuses = db_session.scalars(select(models.ItemStatus)).all()
        assert item_result == []
        assert item_statuses == []

    def test_delete_non_existent_item(self, db_session):
        with pytest.raises(Exception) as exc_info:
            delete_item(barcode="does not exist", db=db_session)
        assert exc_info.type is NotFoundError
