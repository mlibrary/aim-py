from sqlalchemy.orm import Session
from aim import models, schemas

def get_item(db: Session, barcode: str):
    return db.query(models.Item).filter(models.Item.barcode == barcode).first()

def get_items(db: Session, in_zephir: bool | None):
    if in_zephir == True:
        #this is working
        return db.query(models.Item).filter(models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")).all()
    elif in_zephir == False:
        #this is not working
        return db.query(models.Item).filter(~models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")).all()

    return db.query(models.Item).all()


def add_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(barcode=item.barcode)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_status(db: Session, name: str):
    return db.query(models.Status).filter(models.Status.name == name).first()

def get_statuses(db: Session):
    return db.query(models.Status).all()

def add_item_status(db: Session, item: models.Item, status: models.Status):
   db_item_status = models.ItemStatus(item=item, status=status) 
   db.add(db_item_status)
   db.commit()
   db.refresh(item)
   return item
