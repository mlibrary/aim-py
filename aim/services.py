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

    #: The application name
    app_name: str

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

    #: The url in the s3 bucket for the digifeeds process
    digifeeds_s3_input_path: str

    #: The zephir item bib api
    zephir_bib_api_url: str

    #: The path in the s3 bucket for processed barcodes
    digifeeds_s3_processed_path: str

    #: The path in the s3 bucket for processed barcodes of new items that are safe to prune when found in hathifiles
    digifeeds_s3_prunable_path: str

    #: The name of the rclone remote/bucket alias for the s3 input bucket
    digifeeds_s3_rclone_remote: str

    #: The name of the rclone remote for the place where google pickups up the digifeeds files
    digifeeds_pickup_rclone_remote: str

    #: The name of the rclone remote where we put reports about what has been sent to google
    digifeeds_delivery_reports_rclone_remote: str

    #: The name of the rclone remote where we put reports that show what items are in hathitrust
    digifeeds_hathifiles_reports_rclone_remote: str

    # The name of the rclone remote for the fileserver for digifeeds files for DCU
    digifeeds_fileserver_rclone_remote: str

    #: The path to the directory on the fileserver remote for processed barcodes of new items that are safe to prune when found in hathifiles
    digifeeds_fileserver_prunable_path: str

    #: file path to store of the hathi_file_list update items
    hathifiles_store_path: str

    #: url to argo events webhook for triggering the update of the hathifiles database
    hathifiles_webhook_url: str

    #: The Hathifiles MySQL database
    hathifiles_mysql_database: sa.engine.URL

    #: The Hathifiles API URL
    hathifiles_api_url: str


S = Services(
    app_name=os.getenv("APP_NAME") or "aim",
    logger=structlog.get_logger(),
    mysql_database=sa.engine.URL.create(
        drivername="mysql+mysqldb",
        username=os.getenv("MARIADB_USER") or "user",
        password=os.getenv("MARIADB_PASSWORD") or "password",
        host=os.getenv("DATABASE_HOST") or "database",
        database=os.getenv("MARIADB_DATABASE") or "database",
    ),
    test_database="sqlite:///:memory:",
    ci_on=os.getenv("CI"),
    digifeeds_api_url=os.getenv("DIGIFEEDS_API_URL") or "http://api:8000",
    digifeeds_set_id=os.getenv("DIGIFEEDS_SET_ID") or "digifeeds_set_id",
    alma_api_key=os.getenv("ALMA_API_KEY") or "alma_api_key",
    alma_api_url="https://api-na.hosted.exlibrisgroup.com/almaws/v1",
    digifeeds_s3_input_path=os.getenv("DIGIFEEDS_S3_INPUT_PATH")
    or "path/to/input/barcodes",
    zephir_bib_api_url="http://zephir.cdlib.org/api/item",
    digifeeds_s3_processed_path=os.getenv("DIGIFEEDS_S3_PROCESSED_PATH")
    or "path/to/processed/barcodes",
    digifeeds_s3_prunable_path=os.getenv("DIGIFEEDS_S3_PRUNABLE_PATH")
    or "path/to/prunable/barcodes",
    digifeeds_s3_rclone_remote=os.getenv("DIGIFEEDS_S3_RCLONE_REMOTE")
    or "digifeeds_bucket",
    digifeeds_pickup_rclone_remote=os.getenv("DIGIFEEDS_PICKUP_RCLONE_REMOTE")
    or "digifeeds_pickup",
    digifeeds_delivery_reports_rclone_remote=os.getenv(
        "DIGIFEEDS_DELIVERY_REPORTS_RCLONE_REMOTE"
    )
    or "digifeeds_delivery_reports",
    digifeeds_hathifiles_reports_rclone_remote=os.getenv(
        "DIGIFEEDS_HATHIFILES_REPORTS_RCLONE_REMOTE"
    ),
    digifeeds_fileserver_rclone_remote=os.getenv("DIGIFEEDS_FILESERVER_RCLONE_REMOTE")
    or "digifeeds_fileserver",
    digifeeds_fileserver_prunable_path=os.getenv("DIGIFEEDS_FILESERVER_PRUNABLE_PATH")
    or "digifeeds/fileserver/prunable/path",
    hathifiles_store_path=os.getenv("HATHIFILES_STORE_PATH")
    or "tmp/hathi_file_list_store.json",
    hathifiles_webhook_url=os.getenv("HATHIFILES_WEBHOOK_URL")
    or "http://localhost:1200/new_hathifile",
    hathifiles_mysql_database=sa.engine.URL.create(
        drivername="mysql+mysqldb",
        username=os.getenv("HATHIFILES_DB_USER") or "user",
        password=os.getenv("HATHIFILES_DB_PASSWORD") or "password",
        host=os.getenv("HATHIFILES_DB_HOST") or "hathifiles-db",
        database=os.getenv("HATHIFILES_DB_DATABASE") or "database",
    ),
    hathifiles_api_url=os.getenv("HATHIFILES_API_URL") or "http://hathifiles-api:8000",
)
