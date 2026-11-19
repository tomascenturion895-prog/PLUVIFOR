"""estimaciones de huecos (valores calculados, siempre estimado, en su propia tabla)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-19 13:30:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gap_estimates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("obs_date", sa.Date(), nullable=False),
        sa.Column("mm", sa.Numeric(precision=8, scale=2, asdecimal=False), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "observado",
                "referencia",
                "estimado",
                name="gap_estimate_category",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "gap_state",
            sa.Enum(
                "dato",
                "fila_sin_valor",
                "sin_fila",
                name="gap_estimate_state",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("method", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("mm >= 0", name=op.f("ck_gap_estimates_mm_non_negative")),
        sa.CheckConstraint("category = 'estimado'", name=op.f("ck_gap_estimates_always_estimated")),
        sa.CheckConstraint("gap_state <> 'dato'", name=op.f("ck_gap_estimates_fills_a_gap")),
        sa.ForeignKeyConstraint(
            ["station_id"], ["stations.id"], name=op.f("fk_gap_estimates_station_id_stations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gap_estimates")),
        sa.UniqueConstraint("station_id", "obs_date", name=op.f("uq_gap_estimates_station_id")),
    )
    with op.batch_alter_table("gap_estimates", schema=None) as batch_op:
        batch_op.create_index("ix_gap_estimates_obs_date", ["obs_date"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("gap_estimates", schema=None) as batch_op:
        batch_op.drop_index("ix_gap_estimates_obs_date")
    op.drop_table("gap_estimates")
