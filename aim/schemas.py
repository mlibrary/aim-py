from pydantic import BaseModel, Field
from datetime import datetime

class ItemStatus(BaseModel):
    name: str = Field(alias="status_name")
    description: str = Field(alias="status_description")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class ItemBase(BaseModel):
    barcode: str = Field(alias="item_barcode")

    class Config:
        from_attributes = True
        populate_by_name = True

class Item(ItemBase):
    created_at: datetime
    statuses: list[ItemStatus] = []

class ItemCreate(ItemBase):
    pass

class StatusBase(BaseModel):
    name: str


class Status(StatusBase):
    description: str


