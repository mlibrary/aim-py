from types import SimpleNamespace
import os

S = SimpleNamespace()
S.mysql_database = f'mysql+mysqldb://{os.environ["MARIADB_USER"]}:{os.environ["MARIADB_PASSWORD"]}@{os.environ["DATABASE_HOST"]}/{os.environ["MARIADB_DATABASE"]}'
S.test_database = "sqlite:///:memory:"
S.ci_on = os.getenv("CI")
