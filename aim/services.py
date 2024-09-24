from types import SimpleNamespace
import os
import sqlalchemy as sa

S = SimpleNamespace()
S.mysql_database = sa.engine.URL.create(
    drivername="mysql+mysqldb",
    username=os.environ["MARIADB_USER"],
    password=os.environ["MARIADB_PASSWORD"],
    host=os.environ["DATABASE_HOST"],
    database=os.environ["MARIADB_DATABASE"],
)
S.test_database = "sqlite:///:memory:"
S.ci_on = os.getenv("CI")
