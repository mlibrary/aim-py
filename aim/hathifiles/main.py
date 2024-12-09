from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy import text, Connection
from aim.services import S

engine = create_engine(S.hathfiles_mysql_database, pool_pre_ping=True)

description = """
The Hathfiles Database API enables getting information about items in HathiTrust 
"""
app = FastAPI(title="Hathifiles", description=description)


# Dependency
def get_db():  # pragma: no cover
    db = engine.connect()
    try:
        yield db
    finally:
        db.close()


@app.get("/items/{htid}")
def get_item(htid: str, db: Connection = Depends(get_db)):
    """
    Get a Hathifiles Item by HathiTrust id
    """
    query = text(f"SELECT * FROM hf WHERE htid='{htid}'")
    result = db.execute(query)
    item = result.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return item._asdict()
