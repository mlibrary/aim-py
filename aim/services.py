from types import SimpleNamespace
from typing import NamedTuple
import os
import sqlalchemy as sa

Services = NamedTuple(
    "Services",
    [
        ("mysql_database", sa.engine.URL),
        ("test_database", str),
        ("ci_on", str | None),
        ("digifeeds_api_url", str),
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
)

# S = SimpleNamespace()
# S.mysql_database = sa.engine.URL.create(
#     drivername="mysql+mysqldb",
#     username=os.environ["MARIADB_USER"],
#     password=os.environ["MARIADB_PASSWORD"],
#     host=os.environ["DATABASE_HOST"],
#     database=os.environ["MARIADB_DATABASE"],
# )
# S.test_database = "sqlite:///:memory:"
# S.ci_on = os.getenv("CI")
# S.digifeeds_api_url = os.getenv("DIGIFEEDS_API_URL") or "http://api:8000"
