"""Fast API Main
=================
The main document for Fast API
"""

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from aim.digifeeds.database import crud, schemas
from aim.digifeeds.database.crud import NotFoundError, AlreadyExistsError
from aim.services import S
from datetime import datetime

# This is here so SessionLocal won't have a problem in tests in github
if S.ci_on:  # pragma: no cover
    engine = create_engine(S.test_database)
else:  # pragma: no cover
    engine = create_engine(S.mysql_database, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

description = """
The Digifeeds API enables tracking of images sent to HathiTrust and Google
through the digifeeds workflow
"""
tags_metadata = [
    {
        "name": "Digifeeds Database",
        "description": "Digifeeds items and statuses.",
    },
]
app = FastAPI(title="Digifeeds", description=description)


# Dependency
def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


query_description = """
Query items for statuses and dates

Example queries:
* `status:in_zephir` Finds all items **with** status `in_zephir`
* `-status:in_zephir` Finds all items **without** status in_zephir
* `created_at<=2025-11-05` Find all items that were created on or before 2025-11-05
* `status.in_zephir.created_at<=2025-11-05` Find all items with an `in_zephir` status that were created on or before 2025-11-05
* `status:in_zephir status:pending_deletion` Find all items that contain both statuses `in_zephir` and `pending_deletion`.

Operators supported:
|Operator | Description | Example |
|---------|-------------|---------|
| `:` | exact match | `status:in_zephir` or `status.in_zephir.created_at:2025-11-05` |
| `-` | does not match | `-status:in_zephir` |
| `<, >, <=, >=` | greater/less than (only for dates) | `created_at<2025-11-05` or `created_at>=2025-11-05`|

Chained queries are ANDed together.

Modeled after the query language for [Stripe](https://docs.stripe.com/search#search-query-language).
"""


@app.get("/items/", response_model_by_alias=False, tags=["Digifeeds Database"])
def get_items(
    offset: int = Query(0, ge=0, description="Requested offset from the list of pages"),
    limit: int = Query(50, ge=1, description="Requested number of items per page"),
    filter: schemas.ItemFilters = Query(
        None, description="Filters on the items in the database"
    ),
    q: str = Query(None, description=query_description),
    db: Session = Depends(get_db),
) -> schemas.PageOfItems:  # list[schemas.Item]:
    """
    Get the digifeeds items.

    These items can be filtered by whether or not their metadata is in Zephir,
    whether or not they are pending deletion, if they are not in alma, or all of
    them can be fetched.
    """

    db_items = crud.get_items(filter=filter, db=db, offset=offset, limit=limit, query=q)
    return {
        "limit": limit,
        "offset": offset,
        "total": crud.get_items_total(filter=filter, db=db, query=q),
        "items": db_items,
    }


@app.get(
    "/items/{barcode}",
    response_model_by_alias=False,
    responses={
        404: {
            "description": "Bad request: The item doesn't exist",
            "model": schemas.Response404,
        }
    },
    tags=["Digifeeds Database"],
)
def get_item(
    barcode: str = Path(..., description="The barcode of the item"),
    db: Session = Depends(get_db),
) -> schemas.Item:
    """
    Get a digifeeds item.

    The item can be fetched by the barcode of the item.
    """

    try:
        db_item = crud.get_item(barcode=barcode, db=db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.post(
    "/items/{barcode}",
    response_model_by_alias=False,
    responses={
        400: {
            "description": "Bad request: The item already exists",
            "model": schemas.Response400,
        }
    },
    tags=["Digifeeds Database"],
)
def create_item(
    barcode: str = Path(..., description="The barcode of the item"),
    db: Session = Depends(get_db),
) -> schemas.Item:
    """
    Create a digifeeds item.

    The item can be created with the barcode of the item and must not already exist.
    """

    item = schemas.ItemCreate(barcode=barcode)
    try:
        db_item = crud.add_item(item=item, db=db)
    except AlreadyExistsError:
        raise HTTPException(status_code=400, detail="Item already exists")
    else:
        return db_item


desc_put_404 = """
Bad request: The item or status doesn't exist<br><br>
Possible reponses:
<ul>
  <li>Item not found</li>
  <li>Status not found</li>
</ul>
"""


@app.put(
    "/items/{barcode}/status/{status_name}",
    response_model_by_alias=False,
    responses={
        404: {
            "description": desc_put_404,
            "model": schemas.Response404,
        }
    },
    tags=["Digifeeds Database"],
)
def add_item_status(
    barcode: str, status_name: str, db: Session = Depends(get_db)
) -> schemas.Item:
    """
    Update a digifeeds item.

    This is how to add a status to an existing item.
    """

    try:
        db_status = crud.get_status(name=status_name, db=db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Status not found")

    try:
        db_item = crud.get_item(barcode=barcode, db=db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")

    return crud.add_item_status(db=db, item=db_item, status=db_status)


@app.put(
    "/items/{barcode}/hathifiles_timestamp/{timestamp}",
    response_model_by_alias=False,
    responses={
        404: {
            "description": "Bad request: The item doesn't exist",
            "model": schemas.Response404,
        },
    },
    tags=["Digifeeds Database"],
)
def update_hathifiles_timestamp(
    barcode: str, timestamp: datetime, db: Session = Depends(get_db)
) -> schemas.Item:
    try:
        db_item = crud.get_item(barcode=barcode, db=db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        return crud.update_hathifiles_timestamp(
            db=db, item=db_item, timestamp=timestamp
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/items/{barcode}",
    response_model_by_alias=False,
    responses={
        404: {
            "description": "Bad request: The item doesn't exist",
            "model": schemas.Response404,
        }
    },
    tags=["Digifeeds Database"],
)
def delete_item(barcode: str, db: Session = Depends(get_db)) -> schemas.Item:
    try:
        db_item = crud.delete_item(db=db, barcode=barcode)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    S.logger.info(db_item)
    return db_item


@app.get("/statuses", tags=["Digifeeds Database"])
def get_statuses(db: Session = Depends(get_db)) -> list[schemas.Status]:
    """
    Get digifeeds statuses.

    Get a list of statuses.
    """

    db_statuses = crud.get_statuses(db=db)
    return db_statuses
