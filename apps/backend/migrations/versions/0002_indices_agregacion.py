"""índices para consultas de acumulados por zona y por categoría

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19 00:50:00
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("stations", schema=None) as batch_op:
        batch_op.create_index("ix_stations_zone", ["zone"], unique=False)
        batch_op.create_index("ix_stations_department", ["department"], unique=False)
    with op.batch_alter_table("rainfall_records", schema=None) as batch_op:
        batch_op.create_index(
            "ix_rainfall_records_category_obs_date", ["category", "obs_date"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("rainfall_records", schema=None) as batch_op:
        batch_op.drop_index("ix_rainfall_records_category_obs_date")
    with op.batch_alter_table("stations", schema=None) as batch_op:
        batch_op.drop_index("ix_stations_department")
        batch_op.drop_index("ix_stations_zone")
