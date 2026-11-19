"""reportes de campo (lluvia anotada por la policía donde no hay estación)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19 10:30:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("obs_date", sa.Date(), nullable=False),
        sa.Column("mm", sa.Numeric(precision=8, scale=2, asdecimal=False), nullable=False),
        sa.Column("place", sa.String(length=200), nullable=False),
        sa.Column("reporter", sa.String(length=120), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column(
            "location_status",
            sa.Enum(
                "informada",
                "pendiente",
                name="field_report_location",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "location_source",
            sa.Enum(
                "dispositivo",
                "manual",
                name="field_report_location_source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "observado",
                "referencia",
                "estimado",
                name="field_report_category",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "validation",
            sa.Enum(
                "validado",
                "sin_validar",
                name="field_report_validation",
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
        sa.CheckConstraint("mm >= 0", name=op.f("ck_field_reports_mm_non_negative")),
        sa.CheckConstraint(
            "(lat IS NULL) = (lon IS NULL)", name=op.f("ck_field_reports_location_complete")
        ),
        sa.CheckConstraint(
            "lat IS NULL OR (lat BETWEEN -90 AND 90)", name=op.f("ck_field_reports_lat_range")
        ),
        sa.CheckConstraint(
            "lon IS NULL OR (lon BETWEEN -180 AND 180)", name=op.f("ck_field_reports_lon_range")
        ),
        sa.CheckConstraint(
            "(location_status = 'informada') = (lat IS NOT NULL)",
            name=op.f("ck_field_reports_location_status_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_field_reports")),
    )
    with op.batch_alter_table("field_reports", schema=None) as batch_op:
        batch_op.create_index("ix_field_reports_obs_date", ["obs_date"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("field_reports", schema=None) as batch_op:
        batch_op.drop_index("ix_field_reports_obs_date")
    op.drop_table("field_reports")
