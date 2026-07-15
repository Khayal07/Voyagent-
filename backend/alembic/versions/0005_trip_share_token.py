"""trips.share_token — oxu-yalnız paylaşma linki

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("share_token", sa.String(32), nullable=True))
    op.create_index("ix_trips_share_token", "trips", ["share_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_trips_share_token", table_name="trips")
    op.drop_column("trips", "share_token")
