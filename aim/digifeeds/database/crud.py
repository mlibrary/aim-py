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


def get_items_total(db: Session, in_zephir: bool | None):
    query = get_items_query(db=db, in_zephir=in_zephir)
    return query.count()


def get_items(db: Session, in_zephir: bool | None, limit: int, offset: int):
    """
    Get Digifeed items from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        in_zephir (bool | None): Whether or not the items are in zephir

    Returns:
        aim.digifeeds.database.models.Item: Item object
    """
    query = get_items_query(db=db, in_zephir=in_zephir)
    return query.offset(offset).limit(limit).all()


def get_items_query(db: Session, in_zephir: bool | None):
    query = db.query(models.Item)
    if in_zephir is True:
        query = query.filter(
            models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
        )
    elif in_zephir is False:
        query = query.filter(
            ~models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
        )
    return query


def add_item(db: Session, item: schemas.ItemCreate):
    """Add an item to the database. All you need is a barcode.

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        item (schemas.ItemCreate): Item object with a barcode

    Returns:
        aim.digifeeds.database.models.Item: Item object
    """
    db_item = models.Item(barcode=item.barcode)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_status(db: Session, name: str):
    """Gets a given status from the database based on the name

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        name (str): Name of the status

    Returns:
        aim.digifeeds.database.models.Status: Status object
    """
    return db.query(models.Status).filter(models.Status.name == name).first()


def get_statuses(db: Session):
    """Gets statuses from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session

    Returns:
        aim.digifeeds.database.models.Status: Status object
    """
    return db.query(models.Status).all()


def add_item_status(db: Session, item: models.Item, status: models.Status):
    """Add a status to an item in the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        item (models.Item): Item object
        status (models.Status): Status

    Returns:
        aim.digifeeds.database.models.Item: Item object
    """
    db_item_status = models.ItemStatus(item=item, status=status)
    db.add(db_item_status)
    db.commit()
    db.refresh(item)
    return item
