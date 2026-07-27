from aim.google_picklist.alma_client import AlmaClient
from aim.services import S
from functools import reduce
import re


def main(
    input_path=S.google_picklist_input_file_path,
    output_path=S.google_picklist_output_file_path,
):
    with open(input_path) as in_file:
        with open(output_path, "w") as out_file:
            for line in in_file:
                parts = line.strip().split("\t")
                barcode = parts[12]
                row = barcode_to_row(barcode)
                out_file.write(row)


def barcode_to_row(barcode):
    response = AlmaClient().get_barcode(barcode)
    if "not_found" in response:
        return f"barcode not found: {barcode}\n"
    else:
        return AlmaItem(response).row()


class AlmaItem:
    def __init__(self, data):
        self.data = data

    @property
    def mms_id(self):
        return self.safe_get("bib_data", "mms_id")

    @property
    def title(self):
        return self.safe_get("bib_data", "title")

    @property
    def library_code(self):
        return self.safe_get("item_data", "library", "value")

    @property
    def location_code(self):
        return self.safe_get("item_data", "location", "value")

    @property
    def barcode(self):
        return self.safe_get("item_data", "barcode")

    @property
    def call_number(self):
        return self.safe_get("holding_data", "call_number")

    @property
    def description(self):
        return self.safe_get("item_data", "description")

    @property
    def inventory_number(self):
        return self.safe_get("item_data", "inventory_number")

    @property
    def base_status(self):
        return self.safe_get("item_data", "base_status", "desc")

    @property
    def work_order_type(self):
        return self.safe_get("item_data", "work_order_type", "value")

    @property
    def htid(self):
        alternative_call_number = self.safe_get("item_data", "alternative_call_number")
        split_callnumber = re.split(r"\s", alternative_call_number)
        return split_callnumber[0]

    def row(self):
        return (
            "\t".join(
                (
                    self.mms_id,
                    self.title,
                    self.library_code,
                    self.location_code,
                    self.barcode,
                    self.htid,
                    self.call_number,
                    self.description,
                    self.inventory_number,
                    self.base_status,
                    self.work_order_type,
                )
            )
            + "\n"
        )

    def safe_get(self, *keys):
        return (
            reduce(lambda val, key: val.get(key) if val else "", keys, self.data) or ""
        )


def ht_id(item_status):
    return "htid"
