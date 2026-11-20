"""canales de los avisos (WhatsApp, correo y sistema) y correo enmascarado

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-20 16:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

KIND_CHECK = "ck_alert_outbox_alert_message_kind"
CHANNEL_CHECK = "ck_alert_outbox_alert_message_channel"


def upgrade() -> None:
    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email_masked", sa.String(length=120), nullable=True))
    # Primero las columnas; después las restricciones (SQLite reconstruye la tabla en cada lote).
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("channel", sa.String(length=32), nullable=False, server_default="whatsapp")
        )
        batch_op.add_column(sa.Column("recipient", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("subject", sa.String(length=200), nullable=True))
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_constraint(op.f(KIND_CHECK), type_="check")
        batch_op.create_check_constraint(
            op.f(KIND_CHECK), "kind IN ('codigo', 'bienvenida', 'aviso')"
        )
        batch_op.create_check_constraint(
            op.f(CHANNEL_CHECK), "channel IN ('whatsapp', 'email', 'sistema')"
        )


def downgrade() -> None:
    # Las bienvenidas no existían antes: se borran para poder volver a la restricción vieja.
    op.execute("DELETE FROM alert_outbox WHERE kind = 'bienvenida'")
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_constraint(op.f(CHANNEL_CHECK), type_="check")
        batch_op.drop_constraint(op.f(KIND_CHECK), type_="check")
        batch_op.create_check_constraint(op.f(KIND_CHECK), "kind IN ('codigo', 'aviso')")
    with op.batch_alter_table("alert_outbox", schema=None) as batch_op:
        batch_op.drop_column("subject")
        batch_op.drop_column("recipient")
        batch_op.drop_column("channel")
    with op.batch_alter_table("alert_subscriptions", schema=None) as batch_op:
        batch_op.drop_column("email_masked")
