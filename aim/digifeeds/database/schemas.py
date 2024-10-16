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
