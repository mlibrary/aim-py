"""Digifeeds Crud operations
============================

Operations that act on the digifeeds database
"""
from sqlalchemy.orm import Session
from aim.digifeeds.database import schemas
from aim.digifeeds.database import models


def get_item(db: Session, barcode: str):
    """
    Get item from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        barcode (str): Barcode of the item

    Returns:
        aim.digifeeds.database.models.Item: Item object

    """
    return db.query(models.Item).filter(models.Item.barcode == barcode).first()


def get_items(db: Session, in_zephir: bool | None):
    """
    Get Digifeed items from the database

    Args:
        db (Session): _description_
        in_zephir (bool | None): _description_

    Returns:
        _type_: _description_
    """
    if in_zephir is True:
        return (
            db.query(models.Item)
            .filter(
                models.Item.statuses.any(
                    models.ItemStatus.status_name == "in_zephir")
            )
            .all()
        )
    elif in_zephir is False:
        return (
            db.query(models.Item)
            .filter(
                ~models.Item.statuses.any(
                    models.ItemStatus.status_name == "in_zephir")
            )
            .all()
        )

    return db.query(models.Item).all()


def add_item(db: Session, item: schemas.ItemCreate):
    """_summary_

    Args:
        db (Session): _description_
        item (schemas.ItemCreate): _description_

    Returns:
        _type_: _description_
    """
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
