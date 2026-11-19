"""lecturas de sensores (hoy solo simuladas, en su propia tabla)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19 12:30:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mm", sa.Numeric(precision=8, scale=2, asdecimal=False), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "simulado",
                name="sensor_reading_category",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("mm >= 0", name=op.f("ck_sensor_readings_mm_non_negative")),
        sa.CheckConstraint(
            "(lat IS NULL) = (lon IS NULL)", name=op.f("ck_sensor_readings_location_complete")
        ),
        sa.CheckConstraint(
            "lat IS NULL OR (lat BETWEEN -90 AND 90)", name=op.f("ck_sensor_readings_lat_range")
        ),
        sa.CheckConstraint(
            "lon IS NULL OR (lon BETWEEN -180 AND 180)", name=op.f("ck_sensor_readings_lon_range")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sensor_readings")),
        sa.UniqueConstraint("device_id", "read_at", name=op.f("uq_sensor_readings_device_id")),
    )
    with op.batch_alter_table("sensor_readings", schema=None) as batch_op:
        batch_op.create_index("ix_sensor_readings_read_at", ["read_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("sensor_readings", schema=None) as batch_op:
        batch_op.drop_index("ix_sensor_readings_read_at")
    op.drop_table("sensor_readings")
