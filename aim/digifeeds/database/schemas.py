from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ItemStatus(BaseModel):
    name: str = Field(alias="status_name")
    description: str = Field(alias="status_description")
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ItemBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    barcode: str = Field(alias="item_barcode")

class Item(ItemBase):
    created_at: datetime
    statuses: list[ItemStatus] = []

class ItemCreate(ItemBase):
    pass

class StatusBase(BaseModel):
    name: str


class Status(StatusBase):
    description: str


