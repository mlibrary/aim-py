from aim.services import S
from aim.digifeeds.db_client import DBClient
from aim.digifeeds.item import get_item
from pathlib import Path
from rclone_python import rclone
from datetime import datetime, timedelta, date
import csv
import tempfile


def list_barcodes_in_input_bucket():
    files = rclone.ls(
        path=f"{S.digifeeds_s3_rclone_remote}:{S.digifeeds_s3_input_path}",
        files_only=True,
        max_depth=1,
    )
    return [Path(file["Name"]).stem for file in files]


def list_barcodes_potentially_in_hathifiles():
    items = DBClient().get_items(q="status:pending_deletion -status:in_hathifiles")
    if items:
        return [item["barcode"] for item in items]


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
        output.append([filemaker_date(date), barcode])

    return output


def write_and_send_report_to_mayhem(
    content,
    base_name,
    rclone_remote,
    report_file=None,
):
    if not report_file:
        report_file = tempfile.NamedTemporaryFile()

    with open(report_file.name, "w") as rf:
        writer = csv.writer(rf, delimiter="\t", lineterminator="\n")
        S.logger.info("writing_report_rows_to_file")
        writer.writerows(content)

    S.logger.info("writing delivery report")

    today = date.today().isoformat()
    rclone.copyto(
        in_path=report_file.name,
        out_path=f"{rclone_remote}:{today}_{base_name}.txt",
    )


def generate_barcodes_added_in_last_two_weeks_report():
    content = barcodes_added_in_last_two_weeks()
    write_and_send_report_to_mayhem(
        content=content,
        base_name="barcodes_in_s3_processed",
        rclone_remote=S.digifeeds_delivery_reports_rclone_remote,
    )


def barcodes_in_hathifiles_in_last_two_weeks():
    two_weeks_ago = date.today() - timedelta(14)
    items = DBClient().get_items(
        q=f"status.in_hathifiles.created_at>={two_weeks_ago.isoformat()}"
    )
    if items:
        return [
            [
                item["barcode"],
                filemaker_date(item["hathifiles_timestamp"]),
                hathitrust_url(item["barcode"]),
            ]
            for item in items
        ]
    else:
        return []


def generate_barcodes_in_hathifiles_report():
    content = barcodes_in_hathifiles_in_last_two_weeks()
    write_and_send_report_to_mayhem(
        content=content,
        base_name="barcodes_in_hathifiles",
        rclone_remote=S.digifeeds_hathifiles_reports_rclone_remote,
    )


def prune_processed_barcodes(rclone_path: str):
    data_structure = {}
    files_and_directories = rclone.ls(
        path=rclone_path,
        files_only=False,
        max_depth=1,
    )
    for f in files_and_directories:
        barcode = barcode_from_name(f["Name"])
        if barcode not in data_structure:
            data_structure[barcode] = [f]
        else:
            data_structure[barcode].append(f)

    for barcode in data_structure.keys():
        if get_item(barcode).has_status("in_hathifiles"):
            S.logger.info(
                "prune",
                barcode=barcode,
                message="removed because it was found in the hathifiles",
            )
            for item in data_structure[barcode]:
                if item["IsDir"]:
                    rclone.purge(path=f"{rclone_path}/{item['Path']}")
                else:
                    rclone.delete(path=f"{rclone_path}/{item['Path']}")

        else:
            S.logger.info(
                "not_in_hathifiles",
                barcode=barcode,
                message="not pruned because not found in hathifiles",
            )


def barcode_from_name(name):
    return name.split(".")[0].split("_")[-1]


def filemaker_date(datestr: str) -> str:
    date = datetime.fromisoformat(datestr)
    return date.strftime("%m/%d/%Y")


def hathitrust_url(barcode: str) -> str:
    return f"https://babel.hathitrust.org/cgi/pt?id=mdp.{barcode}"
