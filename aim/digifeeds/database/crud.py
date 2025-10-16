"""Digifeeds Crud operations
============================

Operations that act on the digifeeds database
"""

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload
from aim.digifeeds.database import schemas
from aim.digifeeds.database import models
import datetime
import shlex
import re


class NotFoundError(Exception):
    pass


class AlreadyExistsError(Exception):
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


def get_items_total(db: Session, filter: schemas.ItemFilters = None, query: str = None):
    stmnt = get_items_statement(filter=filter)
    stmnt = get_query_statement(query=query, stmnt=stmnt)
    return db.execute(select(func.count()).select_from(stmnt.subquery())).scalar_one()


def get_items(
    db: Session,
    limit: int,
    offset: int,
    filter: schemas.ItemFilters = None,
    query: str = None,
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
    stmnt = get_query_statement(query=query, stmnt=stmnt)
    return db.scalars(stmnt).all()


def get_query_statement(query: str, stmnt):
    if query:
        clauses = shlex.split(query)
        for clause in clauses:
            result = re.match(r"(-)?([\w.]+)([:<>=]{1,2})(.*)", clause).groups()
            negation = result[0] is not None
            field_parts = result[1].split(".")
            field = field_parts[0]

            operator = result[2]
            value = result[3]

            if field == "status":
                if len(field_parts) == 1:
                    status_name = value
                    subfield = None
                else:
                    status_name = field_parts[1]
                    subfield = field_parts[2]

                conditions = [models.ItemStatus.status_name == status_name]
                if subfield:
                    conditions.append(
                        numeric_condition(
                            field=getattr(models.ItemStatus, subfield),
                            value=clean(field=subfield, value=value),
                            operator=operator,
                            negation=negation,
                        )
                    )
                    negation = None

                status_query = models.Item.statuses.any(and_(*conditions))

                if negation:
                    stmnt = stmnt.where(~status_query)
                else:
                    stmnt = stmnt.where(status_query)
            elif is_date(field):
                stmnt = stmnt.where(
                    numeric_condition(
                        field=getattr(models.Item, field),
                        value=clean(field=field, value=value),
                        operator=operator,
                        negation=negation,
                    )
                )
    return stmnt


def show_query(stmnt):
    """
    For debugging
    """
    print(stmnt.compile(compile_kwargs={"literal_binds": True}))


def is_date(field):
    return field in ["created_at", "hathifiles_timestamp"]


def clean(field, value):
    if value in ["null", "NULL"]:
        pass
    elif is_date(field):
        return datetime.date.fromisoformat(value)
    else:
        return value


def numeric_condition(field, value, operator, negation):
    if isinstance(value, datetime.date):
        field = func.DATE(field)

    match operator:
        case "<=":
            return field <= value
        case "<":
            return field < value
        case ">=":
            return field >= value
        case ">":
            return field > value
        case ":":
            if negation:
                return field != value
            else:
                return field == value


def get_items_statement(filter: schemas.ItemFilters = None):
    stmnt = select(models.Item)
    match filter:
        case "in_zephir":
            stmnt = stmnt.where(
                models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
            )
        case "not_in_zephir":
            stmnt = stmnt.where(
                ~models.Item.statuses.any(models.ItemStatus.status_name == "in_zephir")
            )
        case "pending_deletion":
            stmnt = stmnt.where(
                models.Item.statuses.any(
                    models.ItemStatus.status_name == "pending_deletion"
                )
            )
        case "not_pending_deletion":
            stmnt = stmnt.where(
                ~models.Item.statuses.any(
                    models.ItemStatus.status_name == "pending_deletion"
                )
            )
        case "not_found_in_alma":
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

    stmnt = select(models.Item).filter_by(barcode=item.barcode)
    already_in_db_item = db.scalars(stmnt).first()

    if already_in_db_item is not None:
        raise AlreadyExistsError()

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
