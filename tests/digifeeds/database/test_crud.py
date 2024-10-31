from aim.digifeeds.database.crud import (
    get_item,
    get_items,
    add_item,
    get_status,
    get_statuses,
    add_item_status,
)
from aim.digifeeds.database.schemas import ItemCreate


class TestCrud:
    def test_get_item(self, db_session):
        item = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        barcode = item.barcode
        item_in_db = get_item(barcode=barcode, db=db_session)
        assert (item_in_db.barcode) == "valid_barcode"

    def test_get_item_that_does_not_exist(self, db_session):
        item_in_db = get_item(barcode="does not exist", db=db_session)
        assert (item_in_db) is None

    def test_get_items_all(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, in_zephir=None, limit=2, offset=0)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (items[0]) == item1
        assert (items[1]) == item2

    def test_get_items_in_zephir(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, in_zephir=True, limit=2, offset=0)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1

    def test_get_items_not_in_zephir(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        items = get_items(db=db_session, in_zephir=False, limit=2, offset=0)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item2

    def test_get_status_that_exists(self, db_session):
        status = get_status(db=db_session, name="in_zephir")
        assert (status.name) == "in_zephir"

    def test_get_status_that_does_not_exist(self, db_session):
        status = get_status(db=db_session, name="does_not_exist")
        assert (status) is None

    def test_get_statuses(self, db_session):
        statuses = get_statuses(db=db_session)
        assert (len(statuses)) > 1
        assert (statuses[0].name) == "in_zephir"
