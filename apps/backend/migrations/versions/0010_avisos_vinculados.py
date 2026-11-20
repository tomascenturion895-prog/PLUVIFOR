"""avisos vinculados a cuentas y a varias estaciones, con historial de envíos

- `alert_subscriptions.user_id`: la cuenta dueña (se borra en cascada con ella).
- `alert_subscription_stations`: varias estaciones por suscripción (reemplaza a `station_id`; los
  datos existentes se trasladan antes de quitar la columna).
- `alert_dispatches`: historial de avisos enviados; `alert_outbox.dispatch_id` los une a sus
  mensajes.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-20 22:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

FK_STATION = "fk_alert_subscriptions_station_id_stations"
FK_USER = "fk_alert_subscriptions_user_id_users"
FK_DISPATCH = "fk_alert_outbox_dispatch_id_alert_dispatches"


def upgrade() -> None:
    op.create_table(
        "alert_subscription_stations",
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["alert_subscriptions.id"],
            name=op.f("fk_alert_subscription_stations_subscription_id_alert_subscriptions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["stations.id"],
            name=op.f("fk_alert_subscription_stations_station_id_stations"),
        ),
        sa.PrimaryKeyConstraint(
            "subscription_id", "station_id", name=op.f("pk_alert_subscription_stations")
        ),
    )
    with op.batch_alter_table("alert_subscription_stations", schema=None) as batch_op:
        batch_op.create_index(
            "ix_alert_subscription_stations_station_id", ["station_id"], unique=False
        )
    # Lo que cada suscripción había pedido hasta ahora (una estación o ninguna) se conserva.
    op.execute(
        "INSERT INTO alert_subscription_stations (subscription_id, station_id) "
        "SELECT id, station_id FROM alert_subscriptions WHERE station_id IS NOT NULL"
    )

    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_subscriptions_station_id")
        batch_op.drop_constraint(op.f(FK_STATION), type_="foreignkey")
        batch_op.drop_column("station_id")
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f(FK_USER), "users", ["user_id"], ["id"], ondelete="CASCADE")
        batch_op.create_index("ix_alert_subscriptions_user_id", ["user_id"], unique=False)

    op.create_table(
        "alert_dispatches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("obs_date", sa.Date(), nullable=False),
        sa.Column("mm", sa.Float(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("queued", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("mm >= 0", name=op.f("ck_alert_dispatches_mm_non_negative")),
        sa.CheckConstraint("queued >= 0", name=op.f("ck_alert_dispatches_queued_non_negative")),
        sa.ForeignKeyConstraint(
            ["station_id"], ["stations.id"], name=op.f("fk_alert_dispatches_station_id_stations")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_alert_dispatches_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_dispatches")),
    )
    with op.batch_alter_table("alert_dispatches", schema=None) as batch_op:
        batch_op.create_index("ix_alert_dispatches_station_id", ["station_id"], unique=False)
        batch_op.create_index("ix_alert_dispatches_created_at", ["created_at"], unique=False)
        batch_op.create_index(
            "ix_alert_dispatches_created_by_user_id", ["created_by_user_id"], unique=False
        )

    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dispatch_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            op.f(FK_DISPATCH), "alert_dispatches", ["dispatch_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index("ix_alert_outbox_dispatch_id", ["dispatch_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_outbox_dispatch_id")
        batch_op.drop_constraint(op.f(FK_DISPATCH), type_="foreignkey")
        batch_op.drop_column("dispatch_id")
    op.drop_table("alert_dispatches")

    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_subscriptions_user_id")
        batch_op.drop_constraint(op.f(FK_USER), type_="foreignkey")
        batch_op.drop_column("user_id")
        batch_op.add_column(sa.Column("station_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f(FK_STATION), "stations", ["station_id"], ["id"])
        batch_op.create_index("ix_alert_subscriptions_station_id", ["station_id"], unique=False)
    # Volver atrás solo puede guardar una estación por suscripción: se conserva la de menor id.
    op.execute(
        "UPDATE alert_subscriptions SET station_id = ("
        "SELECT MIN(station_id) FROM alert_subscription_stations s "
        "WHERE s.subscription_id = alert_subscriptions.id)"
    )
    op.drop_table("alert_subscription_stations")
