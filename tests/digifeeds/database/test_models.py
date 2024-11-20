from aim.digifeeds.database.models import Item, Status, ItemStatus
from sqlalchemy import select


class TestItem:
    def test_item_valid(self, db_session):
        valid_item = Item(barcode="valid_barcode")
        db_session.add(valid_item)
        db_session.commit()
        stmnt = select(Item).filter_by(barcode="valid_barcode")
        item = db_session.scalars(stmnt).first()
        assert item.barcode == "valid_barcode"
        assert item.created_at

    def test_item_statuses(self, db_session):
        item = Item(barcode="valid_barcode")
        db_session.add(item)
        db_session.commit()
        stmnt = select(Status).filter_by(name="in_zephir")
        status = db_session.scalars(stmnt).first()
        db_session.refresh(item)
        assert (len(item.statuses)) == 0

        item_status = ItemStatus(item=item, status=status)
        db_session.add(item_status)
        db_session.commit()
        db_session.refresh(item)

        assert item.barcode == "valid_barcode"
        assert (len(item.statuses)) == 1
        assert item.statuses[0].created_at
        assert item.statuses[0].status_name == "in_zephir"
