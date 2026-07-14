"""itineraries.lodging — otel xərci təxmini bloku

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-14

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "itineraries",
        sa.Column("lodging", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("itineraries", "lodging")
