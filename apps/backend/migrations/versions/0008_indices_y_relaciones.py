"""índices en las claves foráneas que no los tenían y borrado en cascada de los mensajes de avisos

Auditoría de relaciones (20/11/2026). Sin índice, una clave foránea obliga a recorrer toda la
tabla al consultar por ella (por ejemplo las advertencias de una estación) y al borrar la fila
referida. Además, los mensajes de una suscripción se borran junto con ella.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-20 18:00:00
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

FK_OUTBOX = "fk_alert_outbox_subscription_id_alert_subscriptions"


def upgrade() -> None:
    with op.batch_alter_table("quality_flags", schema=None) as batch_op:
        batch_op.create_index(
            "ix_quality_flags_station_id_range",
            ["station_id", "start_date", "end_date"],
            unique=False,
        )
    with op.batch_alter_table("rainfall_records", schema=None) as batch_op:
        batch_op.create_index("ix_rainfall_records_import_id", ["import_id"], unique=False)
    with op.batch_alter_table("import_logs", schema=None) as batch_op:
        batch_op.create_index("ix_import_logs_source_id", ["source_id"], unique=False)
    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.create_index("ix_alert_subscriptions_station_id", ["station_id"], unique=False)
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.create_index("ix_alert_outbox_subscription_id", ["subscription_id"], unique=False)
        batch_op.drop_constraint(op.f(FK_OUTBOX), type_="foreignkey")
        batch_op.create_foreign_key(
            op.f(FK_OUTBOX),
            "alert_subscriptions",
            ["subscription_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_constraint(op.f(FK_OUTBOX), type_="foreignkey")
        batch_op.create_foreign_key(
            op.f(FK_OUTBOX), "alert_subscriptions", ["subscription_id"], ["id"]
        )
        batch_op.drop_index("ix_alert_outbox_subscription_id")
    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.drop_index("ix_alert_subscriptions_station_id")
    with op.batch_alter_table("import_logs", schema=None) as batch_op:
        batch_op.drop_index("ix_import_logs_source_id")
    with op.batch_alter_table("rainfall_records", schema=None) as batch_op:
        batch_op.drop_index("ix_rainfall_records_import_id")
    with op.batch_alter_table("quality_flags", schema=None) as batch_op:
        batch_op.drop_index("ix_quality_flags_station_id_range")
