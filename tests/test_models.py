from aim.models import Item, Status

class TestItem:
    def test_item_valid(self, db_session):
        valid_item = Item(barcode="valid_barcode")
        db_session.add(valid_item)
        db_session.commit()
        item = db_session.query(Item).filter_by(barcode="valid_barcode").first()
        assert item.barcode == "valid_barcode"

    def test_second_item(self, db_session):
        valid_item = Item(barcode="valid2_barcode")
        db_session.add(valid_item)
        db_session.commit()
        item = db_session.query(Item).filter_by(barcode="valid2_barcode").first()
        breakpoint()
        assert item.barcode == "valid2_barcode"
        
      
  