from aim.services import S
import boto3
from pathlib import Path
from rclone_python import rclone
from datetime import datetime
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


def barcodes_added_in_last_two_weeks():
    files = rclone.ls(
        path=f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}",
        args=["--max-age 14d"],
    )
    output = []
    for file in files:
        barcode = file["Name"].split(".")[0]
        date = datetime.fromisoformat(file["ModTime"]).strftime("%Y-%m-%d")
        output.append([date, barcode])

    return output


def write_barcodes_added_in_last_two_weeks_report(outfile):
    output = barcodes_added_in_last_two_weeks()
    writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
    writer.writerows(output)


def generate_barcodes_added_in_last_two_weeks_report():
    report_file = tempfile.NamedTemporaryFile()
    with open(report_file.name, "w") as rf:
        write_barcodes_added_in_last_two_weeks_report(rf)

    today = datetime.today().strftime("%Y-%m-%d")
    rclone.copyto(
        in_path=report_file.name,
        out_path=f"{S.digifeeds_reports_rclone_remote}:{today}_barcodes_in_s3_bucket.tsv",
    )
