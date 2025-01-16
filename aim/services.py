# from typing import NamedTuple
from dataclasses import dataclass
import os
import sqlalchemy as sa
import structlog
import sys

# Configuring the Logger
shared_processors = [
    # Processors that have nothing to do with output,
    # e.g., add timestamps or log level names.
    structlog.processors.add_log_level,
]

if sys.stderr.isatty():  # pragma: no cover
    # Pretty printing when we run in a terminal session.
    # Automatically prints pretty tracebacks when "rich" is installed

    processors = shared_processors + [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]

else:
    # Print JSON when we run, e.g., in a Docker container.
    # Also print structured tracebacks.

    processors = shared_processors + [
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]

structlog.configure(processors)


@dataclass(frozen=True)
class Services:
    """
    Global Configuration Services
    """

    #: The structured logger
    logger: structlog.stdlib.BoundLogger

    #: The Digifeeds MySQL database
    mysql_database: sa.engine.URL

    #: A sqlite in memory digifeeds database for testing
    test_database: str

    #: Is this being run in Github Actions?
    ci_on: str | None

    #: The Alma API Key
    alma_api_key: str

    #: The Alma API url
    alma_api_url: str

    #: The digifeeds database API URL
    digifeeds_api_url: str

    #: The Alma Set Id for the digifeeds set
    digifeeds_set_id: str

    #: The S3 bucket access key for digifeeds
    digifeeds_s3_access_key: str

    #: The S3 bucket secret access key for digifeeds
    digifeeds_s3_secret_access_key: str

    #: The S3 bucket name for the digifeeds process
    digifeeds_s3_bucket: str

    #: The url in the s3 bucket for the digifeeds process
    digifeeds_s3_input_path: str

    #: The zephir item bib api
    zephir_bib_api_url: str
    #: The url in the s3 bucket for processed barcodes
    digifeeds_s3_processed_path: str

    #: The name of the rclone remote/bucket alias for the s3 input bucket
    digifeeds_s3_rclone_remote: str

    #: The name of the rclone remote for the place where google pickups up the digifeeds files
    digifeeds_pickup_rclone_remote: str

    #: The name of the rclone remote where reports from digifeeds are sent
    digifeeds_reports_rclone_remote: str


S = Services(
    logger=structlog.get_logger(),
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
    digifeeds_s3_access_key=os.getenv("DIGIFEEDS_S3_ACCESS_KEY")
    or "digifeeds_s3_access_key",
    digifeeds_s3_secret_access_key=os.getenv("DIGIFEEDS_S3_SECRET_ACCESS_KEY")
    or "digifeeds_s3_secret_access_key",
    digifeeds_s3_bucket=os.getenv("DIGIFEEDS_S3_BUCKET") or "digifeeds_s3_bucket",
    digifeeds_s3_input_path=os.getenv("DIGIFEEDS_S3_INPUT_PATH")
    or "path_to_input_barcodes",
    zephir_bib_api_url="http://zephir.cdlib.org/api/item",
    digifeeds_s3_processed_path=os.getenv("DIGIFEEDS_S3_PROCESSED_PATH")
    or "path_to_processed_barcodes",
    digifeeds_s3_rclone_remote=os.getenv("DIGIFEEDS_S3_RCLONE_REMOTE")
    or "digifeeds_bucket",
    digifeeds_pickup_rclone_remote=os.getenv("DIGIFEEDS_PICKUP_RCLONE_REMOTE")
    or "digifeeds_pickup",
    digifeeds_reports_rclone_remote=os.getenv("DIGIFEEDS_REPORTS_RCLONE_REMOTE")
    or "digifeeds_reports",
)
