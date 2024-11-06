"""Creating initial tables

Revision ID: bbb334fc10e7
Revises:
Create Date: 2024-09-19 18:37:32.652676

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bbb334fc10e7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "items",
        sa.Column("barcode", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("barcode"),
        sa.UniqueConstraint("barcode"),
    )
    op.create_table(
        "statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(length=499), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "item_statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_barcode", sa.String(length=256), nullable=False),
        sa.Column("status_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["item_barcode"],
            ["items.barcode"],
        ),
        sa.ForeignKeyConstraint(
            ["status_id"],
            ["statuses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("item_statuses")
    op.drop_table("statuses")
    op.drop_table("items")
    # ### end Alembic commands ###
