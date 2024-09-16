from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from datetime import datetime

class Base(DeclarativeBase):
  pass

class Item(Base):
    __tablename__ = 'items'

    barcode:  Mapped[str] = mapped_column(String(256), unique=True, primary_key=True)
    statuses: Mapped[list["ItemStatus"]] = relationship()

class Status(Base):
    __tablename__ = 'statuses'
    id:  Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
    description:  Mapped[str] = mapped_column(String(499))

class ItemStatus(Base):
    __tablename__ = 'item_statuses'
    item_barcode: Mapped[int] = mapped_column(ForeignKey('items.barcode'), primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('statuses.id'), primary_key=True)

    item: Mapped["Item"] = relationship(back_populates="statuses")
    status: Mapped["Status"] = relationship()

def load_statuses(session: Session):
    objects = [
        Status(name="in_zephir", description="Item is in zephir"),
        Status(name="added_to_digifeeds_set", description="Item has been added to the digifeeds set"),
        Status(name="copying_start", description="The process for zipping and copying an item to the pickup location has started"),
        Status(name="copying_end", description="The process for zipping and copying an item to the pickup location has completed successfully"),
        Status(name="pending_deletion", description="The item has been copied to the pickup location and can be deleted upon ingest confirmation"),
    ]
    session.bulk_save_objects(objects)
    session.commit()