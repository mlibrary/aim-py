"""Digifeeds Pydantic Models"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


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


class PageOfItems(BaseModel):
    items: list[Item]
    limit: int = 10
    offset: int = 0
    total: int = 1


class ItemFilters(str, Enum):
    in_zephir = "in_zephir"
    not_in_zephir = "not_in_zephir"
    pending_deletion = "pending_deletion"
    not_pending_deletion = "not_pending_deletion"
    not_found_in_alma = "not_found_in_alma"


class ItemCreate(ItemBase):
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
