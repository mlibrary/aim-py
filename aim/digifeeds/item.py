class Item:
    def __init__(self, data: dict) -> None:
        self.data = data

    def has_status(self, status: str) -> bool:
        return any(s["name"] == status for s in self.data["statuses"])

    @property
    def barcode(self) -> str:
        return self.data["barcode"]
