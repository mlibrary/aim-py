"""Fast API Main
=================
The main document for Fast API
"""

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from aim.digifeeds.database import crud, schemas
from aim.services import S

# This is here so SessionLocal won't have a problem in tests in github
if S.ci_on:  # pragma: no cover
    engine = create_engine(S.test_database)
else:  # pragma: no cover
    engine = create_engine(S.mysql_database)

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


@app.get("/items/", response_model_by_alias=False, tags=["Digifeeds Database"])
def get_items(
    in_zephir: bool | None = Query(
        None, description="Filter for items that do or do not have metadata in Zephir"
    ),
    db: Session = Depends(get_db),
) -> list[schemas.Item]:
    """
    Get the digifeeds items.

    These items can be filtered by whether or not their metadata is in Zephir or
    all of them can be fetched.
    """

    db_items = crud.get_items(in_zephir=in_zephir, db=db)
    return db_items


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

    db_item = crud.get_item(barcode=barcode, db=db)
    if db_item is None:
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
    db_item = crud.get_item(barcode=item.barcode, db=db)
    if db_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    db_item = crud.add_item(item=item, db=db)
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
def update_item(
    barcode: str, status_name: str, db: Session = Depends(get_db)
) -> schemas.Item:
    """
    Update a digifeeds item.

    This is how to add a status to an existing item.
    """

    db_status = crud.get_status(name=status_name, db=db)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    db_item = crud.get_item(barcode=barcode, db=db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.add_item_status(db=db, item=db_item, status=db_status)


@app.get("/statuses", tags=["Digifeeds Database"])
def get_statuses(db: Session = Depends(get_db)) -> list[schemas.Status]:
    """
    Get digifeeds statuses.

    Get a list of statuses.
    """

    db_statuses = crud.get_statuses(db=db)
    return db_statuses
