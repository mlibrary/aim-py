"""
Digifeeds Models
================ 
"""

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy.ext.associationproxy import association_proxy
import datetime


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = 'items'

    barcode:  Mapped[str] = mapped_column(
        String(256), unique=True, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    statuses: Mapped[list["ItemStatus"]] = relationship()


class Status(Base):
    __tablename__ = 'statuses'
    id:  Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
    description:  Mapped[str] = mapped_column(String(499))
    items: Mapped[list["ItemStatus"]] = relationship()

    def __repr__(self):
        return (f'Status(id={self.id}, name={self.name}, description={self.description})')


class ItemStatus(Base):
    __tablename__ = 'item_statuses'
    item_barcode: Mapped[int] = mapped_column(
        ForeignKey('items.barcode'), primary_key=True)
    status_id: Mapped[int] = mapped_column(
        ForeignKey('statuses.id'), primary_key=True)
    # https://docs.sqlalchemy.org/en/20/core/functions.html#sqlalchemy.sql.functions.now Tell the db to set the date.
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    item: Mapped["Item"] = relationship(back_populates="statuses")
    status: Mapped["Status"] = relationship(back_populates="items")

    # proxies
    status_name = association_proxy(target_collection="status", attr="name")
    status_description = association_proxy(
        target_collection="status", attr="description")


def load_statuses(session: Session):
    statuses = [
        {"name": "in_zephir", "description": "Item is in zephir"},
        {"name": "added_to_digifeeds_set",
            "description": "Item has been added to the digifeeds set"},
        {"name": "copying_start",
            "description": "The process for zipping and copying an item to the pickup location has started"},
        {"name": "copying_end", "description": "The process for zipping and copying an item to the pickup location has completed successfully"},
        {"name": "pending_deletion",
            "description": "The item has been copied to the pickup location and can be deleted upon ingest confirmation"},
        {"name": "not_found_in_alma", "description": "Barcode wasn't found in Alma"},
    ]
    objects = []
    for status in statuses:
        sts = session.query(Status).filter_by(name=status["name"]).first()
        if sts is None:
            objects.append(Status(**status))

    print(f"Statuses to load: {objects}")

    session.bulk_save_objects(objects)
    session.commit()

    print("Statuses loaded.")
