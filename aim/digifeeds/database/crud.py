"""Digifeeds Crud operations
============================

Operations that act on the digifeeds database
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from aim.digifeeds.database import schemas
from aim.digifeeds.database import models


class NotFoundError(Exception):
    pass


def get_item(db: Session, barcode: str):
    """
    Get item from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        barcode (str): Barcode of the item

    Returns:
        aim.digifeeds.database.models.Item: Item object

    """
    stmnt = (
        select(models.Item)
        .filter_by(barcode=barcode)
        .options(
            # this is here so when we delete the barcode the statuses show up in the output
            joinedload(models.Item.statuses)
        )
    )

    item = db.scalars(stmnt).first()
    if item is None:
        raise NotFoundError()
    else:
        return item


def get_items_total(db: Session, filter: schemas.ItemFilters = None):
    stmnt = get_items_statement(filter=filter)
    return db.execute(select(func.count()).select_from(stmnt.subquery())).scalar_one()


def get_items(
    db: Session,
    limit: int,
    offset: int,
    filter: schemas.ItemFilters = None,
):
    """
    Get Digifeed items from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session
        filter (schemas.ItemFilters | None): filter to apply to the list of items.

    Returns:
        aim.digifeeds.database.models.Item: Item object
    """
    stmnt = get_items_statement(filter=filter).offset(offset).limit(limit)
    return db.scalars(stmnt).all()


def get_items_statement(filter: schemas.ItemFilters = None):
    stmnt = select(models.Item)

    if filter == "in_zephir":
        stmnt = stmnt.where(
            models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
        )
    elif filter == "not_in_zephir":
        stmnt = stmnt.where(
            ~models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
        )
    elif filter == "pending_deletion":
        stmnt = stmnt.where(
            models.Item.statuses.any(
                models.ItemStatus.status_name == "pending_deletion"
            )
        )
    elif filter == "not_pending_deletion":
        stmnt = stmnt.where(
            ~models.Item.statuses.any(
                models.ItemStatus.status_name == "pending_deletion"
            )
        )
    elif filter == "not_found_in_alma":
        stmnt = stmnt.where(
            models.Item.statuses.any(
                models.ItemStatus.status_name == "not_found_in_alma"
            )
        )
    return stmnt


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
    stmnt = select(models.Status).filter_by(name=name)

    status = db.scalars(stmnt).first()
    if status is None:
        raise NotFoundError()
    else:
        return status


def get_statuses(db: Session):
    """Gets statuses from the database

    Args:
        db (sqlalchemy.orm.Session): Digifeeds database session

    Returns:
        aim.digifeeds.database.models.Status: Status object
    """
    return db.scalars(select(models.Status)).all()


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


def delete_item(db: Session, barcode: str):
    db_item = get_item(db=db, barcode=barcode)
    # need to load this now so the statuses show up in the return
    item = schemas.Item(**db_item.__dict__)
    db.delete(db_item)
    db.commit()
    return item
