"""Create click event table with correct fields

Revision ID: d9a1f83dda85
Revises: 22800dc4909d
Create Date: 2025-06-24 21:33:44.565299

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "d9a1f83dda85"
down_revision: Union[str, Sequence[str], None] = "22800dc4909d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("clickevent")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "clickevent",
        sa.Column(
            "id_address", sa.VARCHAR(length=45), autoincrement=False, nullable=True
        ),
        sa.Column(
            "user_agent", sa.VARCHAR(length=500), autoincrement=False, nullable=True
        ),
        sa.Column(
            "referer", sa.VARCHAR(length=500), autoincrement=False, nullable=True
        ),
        sa.Column("country", sa.VARCHAR(length=2), autoincrement=False, nullable=True),
        sa.Column(
            "device_type", sa.VARCHAR(length=20), autoincrement=False, nullable=True
        ),
        sa.Column("browser", sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("link_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "clicked_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["link_id"], ["link.id"], name=op.f("clickevent_link_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("clickevent_pkey")),
    )
    # ### end Alembic commands ###
