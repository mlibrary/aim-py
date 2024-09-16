from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from python_starter.models import Item, Status, ItemStatus
import pytest


@pytest.fixture(scope="module")
def valid_item():
    valid_item = Item(
        barcode="valid_barcode",
    )
    return valid_item

@pytest.fixture(scope="module")
def valid_status():
    valid_status = Status(
        name="VALID_NAME",
        description = "valid_description"
    )
    return valid_status

class TestItem:
    def test_item_valid(self, db_session, valid_item):   
        db_session.add(valid_item)
        db_session.commit()
        item = db_session.query(Item).filter_by(barcode="valid_barcode").first()
        assert item.barcode == "valid_barcode"

    def test_add_item_status(self, db_session, valid_item, valid_status):
        db_session.add(valid_status)
        db_session.add(valid_item)
        db_session.commit()
        status = db_session.query(Status).filter_by(name="VALID_NAME").first()
        item = db_session.query(Item).filter_by(barcode="valid_barcode").first()
        assc = ItemStatus()
        assc.status = status
        assc.item = item
        db_session.add(assc)
        db_session.commit()
        item = db_session.query(Item).filter_by(barcode="valid_barcode").first()
        assert item.statuses[0].status.name == "VALID_NAME"

        

        

class TestStatus:
    def test_status_valid(self, db_session, valid_status):   
        db_session.add(valid_status)
        db_session.commit()
        status = db_session.query(Status).filter_by(name="VALID_NAME").first()
        assert status.name == "VALID_NAME"
        assert status.description == "valid_description"

#     @pytest.mark.xfail(raises=IntegrityError)
#     def test_author_no_email(self, db_session):
#         author = Author( firstname="James", lastname="Clear")
#         db_session.add(author)
#         try: 
#             db_session.commit()
#         except IntegrityError:
#             db_session.rollback()