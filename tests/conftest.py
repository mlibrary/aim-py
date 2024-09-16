# conftest.py
# from https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from python_starter.models import Base


TEST_DB_NAME = "testdb"

@pytest.fixture(scope="session")
def connection(request):
    # Modify this URL according to your database backend
    url = "mysql+mysqldb://root:password@database" 
    engine = create_engine(url)

    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {TEST_DB_NAME} CHARACTER SET = 'utf8'"))

    # Create a new engine/connection that will actually connect
    # to the test database we just created. This will be the
    # connection used by the test suite run.
    engine = create_engine(
        f"{url}/{TEST_DB_NAME}"
    )
    connection = engine.connect()

    def teardown():
        connection.execute(text(f"DROP DATABASE {TEST_DB_NAME}"))
        connection.close()

    request.addfinalizer(teardown)
    return connection

@pytest.fixture(scope="session", autouse=True)
def setup_db(connection, request):
    """Setup test database.

    Creates all database tables as declared in SQLAlchemy models,
    then proceeds to drop all the created tables after all tests
    have finished running.
    """
    # Base.metadata.bind = connection
    Base.metadata.create_all(bind=connection)

    def teardown():
        Base.metadata.drop_all(bind=connection)

    request.addfinalizer(teardown)

@pytest.fixture(scope="module")
def db_session(connection):
    session = sessionmaker(bind=connection)()
    yield session
    session.rollback()
    session.close()