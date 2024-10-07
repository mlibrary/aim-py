from fastapi import Depends, FastAPI, HTTPException
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
app = FastAPI(title="Digifeeds", description=description)


# Dependency
def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/items/", response_model_by_alias=False)
def get_items(
    in_zephir: bool | None = None, db: Session = Depends(get_db)
) -> list[schemas.Item]:
    db_items = crud.get_items(in_zephir=in_zephir, db=db)
    return db_items


@app.get("/items/{barcode}", response_model_by_alias=False)
def get_item(barcode: str, db: Session = Depends(get_db)) -> schemas.Item:
    db_item = crud.get_item(barcode=barcode, db=db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.post("/items/{barcode}", response_model_by_alias=False)
def create_item(barcode: str, db: Session = Depends(get_db)) -> schemas.Item:
    item = schemas.ItemCreate(barcode=barcode)
    db_item = crud.get_item(barcode=item.barcode, db=db)
    if db_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    db_item = crud.add_item(item=item, db=db)
    return db_item


@app.put("/items/{barcode}/status/{status_name}", response_model_by_alias=False)
def update_item(
    barcode: str, status_name: str, db: Session = Depends(get_db)
) -> schemas.Item:
    db_status = crud.get_status(name=status_name, db=db)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    db_item = crud.get_item(barcode=barcode, db=db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.add_item_status(db=db, item=db_item, status=db_status)


@app.get("/statuses")
def get_statuses(db: Session = Depends(get_db)) -> list[schemas.Status]:
    db_statuses = crud.get_statuses(db=db)
    return db_statuses
