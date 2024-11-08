from typing import NamedTuple
import os
import sqlalchemy as sa


class Services(NamedTuple):
    """
    Global Configuration Services
    """

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

    #: The name of the google drive rclone remote where google picks up items
    digifeeds_gdrive_rclone_remote: str


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
    digifeeds_gdrive_rclone_remote=os.getenv("DIGIFEEDS_GDRIVE_RCLONE_REMOTE")
    or "digifeeds_gdrive",
)
