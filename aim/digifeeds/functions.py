from aim.services import S
import boto3
from pathlib import Path
from rclone_python import rclone
from datetime import datetime, timedelta
import csv
import tempfile


def list_barcodes_in_input_bucket():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S.digifeeds_s3_access_key,
        aws_secret_access_key=S.digifeeds_s3_secret_access_key,
    )
    prefix = S.digifeeds_s3_input_path + "/"
    response = s3.list_objects_v2(Bucket=S.digifeeds_s3_bucket, Prefix=prefix)
    barcodes = [Path(object["Key"]).stem for object in response["Contents"]]
    return barcodes


def last_two_weeks_rclone_filter(start_date: datetime = datetime.today()):
    day_count = 14
    dates = []
    for single_date in (start_date - timedelta(n) for n in range(day_count)):
        formatted_date = single_date.strftime("%Y-%m-%d")
        dates.append(f"{formatted_date}*")
    joined = ",".join(dates)
    return f"{{{joined}}}"


def barcodes_added_in_last_two_weeks():
    files = rclone.ls(
        path=f"{S.digifeeds_s3_bucket}:{S.digifeeds_s3_processed_path}",
        args=[f'--include "{last_two_weeks_rclone_filter()}"'],
    )
    output = []
    for file in files:
        barcode = file["Name"].split("_")[2].split(".")[0]
        date = file["Name"].split("_")[0]
        S.logger.info(
            "added_to_barcode_report",
            barcode=barcode,
            message="Added to barcode report",
        )
        output.append([date, barcode])

    return output


def write_barcodes_added_in_last_two_weeks_report(outfile):
    output = barcodes_added_in_last_two_weeks()
    writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
    S.logger.info("writing_report_rows_to_file")
    writer.writerows(output)


def generate_barcodes_added_in_last_two_weeks_report():
    report_file = tempfile.NamedTemporaryFile()
    with open(report_file.name, "w") as rf:
        write_barcodes_added_in_last_two_weeks_report(rf)

    today = datetime.today().strftime("%Y-%m-%d")
    S.logger.info("writing delivery report")
    rclone.copyto(
        in_path=report_file.name,
        out_path=f"{S.digifeeds_delivery_reports_rclone_remote}:{today}_barcodes_in_s3_processed.tsv",
    )
