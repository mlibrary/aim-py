from aim.services import S
from pathlib import Path
from rclone_python import rclone
from datetime import datetime, timedelta
import csv
import tempfile


def list_barcodes_in_input_bucket():
    files = rclone.ls(
        path=f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}",
        files_only=True,
        max_depth=1,
    )
    return [Path(file["Name"]).stem for file in files]


def last_two_weeks_rclone_filter(start_date: datetime = datetime.today()):
    day_count = 14
    dates = []
    for single_date in (start_date - timedelta(n) for n in range(day_count)):
        formatted_date = single_date.strftime("%Y-%m-%d")
        dates.append(f"{formatted_date}*")
    joined = ",".join(dates)
    return f"{{{joined}}}"


def barcodes_added_in_last_two_weeks():
    def format_date(date_string: str):
        date = datetime.strptime(date_string, "%Y-%m-%d")
        return date.strftime("%m/%d/%Y")

    files = rclone.ls(
        path=f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_processed_path}",
        args=[f'--include "{last_two_weeks_rclone_filter()}"'],
        files_only=True,
        max_depth=2,
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
        output.append([format_date(date), barcode])

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
        out_path=f"{S.digifeeds_delivery_reports_rclone_remote}:{today}_barcodes_in_s3_processed.txt",
    )
