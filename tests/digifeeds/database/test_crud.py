from aim.digifeeds.database.crud import (
    get_item,
    get_items,
    add_item,
    get_status,
    get_statuses,
    add_item_status,
    get_items_total,
    delete_item,
    update_hathifiles_timestamp,
    NotFoundError,
)
from aim.digifeeds.database import models
from sqlalchemy import select
from aim.digifeeds.database.schemas import ItemCreate
import datetime
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

    def test_get_items_for_query_pending_deletion(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="pending_deletion")
        add_item_status(db=db_session, item=item1, status=status)

        query = "status:pending_deletion"

        items = get_items(db=db_session, query=query, limit=2, offset=0)
        count = get_items_total(db=db_session, query=query)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1
        assert count == 1

    def test_get_items_for_query_with_2_clauses(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="pending_deletion")
        status2 = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=item1, status=status)
        add_item_status(db=db_session, item=item1, status=status2)
        add_item_status(db=db_session, item=item2, status=status)

        query = "status:pending_deletion status:in_zephir"

        items = get_items(db=db_session, query=query, limit=3, offset=0)
        count = get_items_total(db=db_session, query=query)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item1
        assert count == 1

    def test_get_items_handles_negative_query(self, db_session):
        item1 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        item2 = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        status = get_status(db=db_session, name="pending_deletion")
        add_item_status(db=db_session, item=item1, status=status)

        query = "-status:pending_deletion"

        items = get_items(db=db_session, query=query, limit=2, offset=0)
        count = get_items_total(db=db_session, query=query)
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert (len(items)) == 1
        assert (items[0]) == item2
        assert count == 1

    def test_get_items_handles_date_queries(self, db_session):
        earlier = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        later = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        earlier.created_at = today
        later.created_at = tomorrow
        db_session.commit()
        db_session.refresh(earlier)
        db_session.refresh(later)

        # <=
        query = f'created_at<="{today.isoformat()}"'

        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == earlier

        # <
        query = f'created_at<"{today.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 0

        query = f'created_at<"{tomorrow.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == earlier

        # >=
        query = f'created_at>="{today.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 2

        query = f'created_at>="{tomorrow.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == later

        # >=
        query = f'created_at>"{today.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == later

        query = f'created_at>"{tomorrow.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 0

        # :
        query = f'created_at:"{today.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == earlier

        query = f'created_at:"{tomorrow.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == later

        # - :
        query = f'-created_at:"{today.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == later

        query = f'-created_at:"{tomorrow.isoformat()}"'
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == earlier

    def test_get_items_with_null_date(self, db_session):
        regular_date = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        null_date = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))
        regular_date.hathifiles_timestamp = datetime.datetime.now()
        db_session.commit()
        db_session.refresh(regular_date)
        db_session.refresh(null_date)

        query = "hathifiles_timestamp:null"
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == null_date

        query = "-hathifiles_timestamp:null"
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == regular_date

    def test_get_items_where_status_has_date(self, db_session):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        earlier = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        later = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode2"))

        status = get_status(db=db_session, name="pending_deletion")
        add_item_status(db=db_session, item=earlier, status=status)
        add_item_status(db=db_session, item=later, status=status)

        earlier.statuses[0].created_at = today
        later.statuses[0].created_at = tomorrow

        db_session.commit()
        db_session.refresh(earlier)
        db_session.refresh(later)

        query = f"status.pending_deletion.created_at<={today.isoformat()}"
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == earlier

        query = f"status.pending_deletion.created_at<={tomorrow.isoformat()}"
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 2

    def test_get_items_where_status_has_negated_date(self, db_session):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        pending_today = add_item(
            db=db_session, item=ItemCreate(barcode="valid_barcode")
        )
        pending_tomorrow = add_item(
            db=db_session, item=ItemCreate(barcode="valid_barcode2")
        )

        pd_status = get_status(db=db_session, name="pending_deletion")
        z_status = get_status(db=db_session, name="in_zephir")
        add_item_status(db=db_session, item=pending_today, status=pd_status)
        add_item_status(db=db_session, item=pending_tomorrow, status=pd_status)
        add_item_status(db=db_session, item=pending_tomorrow, status=z_status)

        pending_today.statuses[0].created_at = today
        pending_tomorrow.statuses[0].created_at = tomorrow
        pending_tomorrow.statuses[1].created_at = today

        db_session.commit()
        db_session.refresh(pending_today)
        db_session.refresh(pending_tomorrow)

        query = f"-status.pending_deletion.created_at:{tomorrow.isoformat()}"
        items = get_items(db=db_session, query=query, limit=2, offset=0)
        assert (len(items)) == 1
        assert (items[0]) == pending_today

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

    def test_update_hathifiles_timestamp(self, db_session):
        item = add_item(db=db_session, item=ItemCreate(barcode="valid_barcode"))
        timestamp = datetime.datetime.today()

        result = update_hathifiles_timestamp(
            db=db_session, item=item, timestamp=timestamp
        )

        db_session.refresh(item)

        assert result.hathifiles_timestamp == timestamp
        assert item.hathifiles_timestamp == timestamp
        assert "in_hathifiles" in [status.status_name for status in item.statuses]
