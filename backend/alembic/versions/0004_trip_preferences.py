"""trips.must_visit / avoid / pace — istifadəçi seçimləri

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("must_visit", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    op.add_column(
        "trips",
        sa.Column("avoid", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True),
    )
    op.add_column(
        "trips",
        sa.Column("pace", sa.String(10), nullable=False, server_default="normal"),
    )


def downgrade() -> None:
    op.drop_column("trips", "pace")
    op.drop_column("trips", "avoid")
    op.drop_column("trips", "must_visit")
