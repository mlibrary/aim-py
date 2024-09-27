from typing import NamedTuple
import os
import sqlalchemy as sa

Services = NamedTuple(
    "Services",
    [
        ("mysql_database", sa.engine.URL),
        ("test_database", str),
        ("ci_on", str | None),
        ("alma_api_key", str),
        ("alma_api_url", str),
        ("digifeeds_api_url", str),
        ("digifeeds_set_id", str),
    ],
)

S = Services(
    mysql_database=sa.engine.URL.create(
        drivername="mysql+mysqldb",
        username=os.environ["MARIADB_USER"],
        password=os.environ["MARIADB_PASSWORD"],
        host=os.environ["DATABASE_HOST"],
        database=os.environ["MARIADB_DATABASE"],
    ),
    test_database="sqlite:///:memory:",
    ci_on=os.getenv("CI"),
    digifeeds_api_url=os.getenv("DIGIFEEDS_API_URL") or "http://api:8000",
    digifeeds_set_id=os.getenv("DIGIFEEDS_SET_ID") or "digifeeds_set_id",
    alma_api_key=os.getenv("ALMA_API_KEY") or "alma_api_key",
    alma_api_url="https://api-na.hosted.exlibrisgroup.com/almaws/v1",
)
