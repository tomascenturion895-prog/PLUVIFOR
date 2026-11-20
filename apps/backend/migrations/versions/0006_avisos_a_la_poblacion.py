"""suscripciones a avisos y bandeja simulada de mensajes

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-20 12:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone_hash", sa.String(length=64), nullable=False),
        sa.Column("phone_last4", sa.String(length=4), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pendiente",
                "confirmada",
                "baja",
                name="alert_subscription_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(length=64), nullable=True),
        sa.Column("code_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempts >= 0", name=op.f("ck_alert_subscriptions_attempts_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["station_id"], ["stations.id"], name=op.f("fk_alert_subscriptions_station_id_stations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_subscriptions")),
        sa.UniqueConstraint("phone_hash", name=op.f("uq_alert_subscriptions_phone_hash")),
    )
    op.create_table(
        "alert_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "codigo",
                "aviso",
                name="alert_message_kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("category = 'simulado'", name=op.f("ck_alert_outbox_always_simulated")),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["alert_subscriptions.id"],
            name=op.f("fk_alert_outbox_subscription_id_alert_subscriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_outbox")),
    )
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.create_index("ix_alert_outbox_created_at", ["created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_outbox_created_at")
    op.drop_table("alert_outbox")
    op.drop_table("alert_subscriptions")
