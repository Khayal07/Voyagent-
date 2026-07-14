"""kv_cache — geocode/POI nəticələrinin davamlı cache-i

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-14

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kv_cache",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("value", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("kv_cache")
