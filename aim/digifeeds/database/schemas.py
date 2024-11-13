"""Digifeeds Pydantic Models"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ItemStatus(BaseModel):
    """
    Model of an individual ItemStatus. it includes the name,
    description, and creation date of the status for a given item. It is used
    for listing the statuses for a given Item.
    """

    name: str = Field(alias="status_name")
    description: str = Field(alias="status_description")
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ItemBase(BaseModel):
    """
    Model of the most basic Item. One that only has a barcode. It's
    used as the base for a full Item listing, and for Item creation where
    barcode is the only necessary attribute.
    """

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    barcode: str = Field(alias="item_barcode")


class Item(ItemBase):
    """
    Model for the full listing of an item. It inherits from ItemBase
    which only has a barcode.
    """

    created_at: datetime
    statuses: list[ItemStatus] = []
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "barcode": "39015040218748",
                    "created_at": "2024-09-25T17:12:39",
                    "statuses": [
                        {
                            "name": "in_zephir",
                            "description": "Item is in zephir",
                            "created_at": "2024-09-25T17:13:28",
                        }
                    ],
                }
            ]
        }
    )


class ItemCreate(ItemBase):
    """
    Model for Item creation. Only a Barcode is needed for creating an
    item, so it is identical to ItemBase
    """

    pass


class StatusBase(BaseModel):
    name: str


class Status(StatusBase):
    description: str


class Response(BaseModel):
    detail: str


class Response400(Response):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Item already exists",
                }
            ]
        }
    )


class Response404(Response):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Item not found",
                }
            ]
        }
    )
