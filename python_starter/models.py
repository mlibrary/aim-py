from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from datetime import datetime

class Base(DeclarativeBase):
  pass

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int]  = mapped_column(Integer(), primary_key=True, autoincrement=True)
    barcode:  Mapped[str] = mapped_column(String(100))
    statuses: Mapped[list["ItemStatus"]] = relationship()

class Status(Base):
    __tablename__ = 'statuses'
    id:  Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(254))
    description:  Mapped[str] = mapped_column(String(499))

class ItemStatus(Base):
    __tablename__ = 'item_statuses'
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('statuses.id'), primary_key=True)

    item: Mapped["Item"] = relationship(back_populates="statuses")
    status: Mapped["Status"] = relationship()



# engine = create_engine("mysql+mysqldb://user:password@database/database", pool_recycle=3600, echo=True)
# Session = sessionmaker(bind=engine)