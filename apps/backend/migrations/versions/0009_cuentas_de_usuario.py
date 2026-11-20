"""cuentas de usuario, sesiones y quién cargó cada reporte e importación

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-20 20:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

# Tablas que ahora registran quién hizo la carga (nulo = la clave de administración o el sistema).
AUDITADAS = ("field_reports", "import_logs")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column(
            "role",
            sa.Enum(
                "ciudadano",
                "operador",
                "administrador",
                name="user_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "failed_attempts >= 0", name=op.f("ck_users_failed_attempts_non_negative")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_sessions_token_hash")),
    )
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.create_index("ix_auth_sessions_user_id", ["user_id"], unique=False)

    for tabla in AUDITADAS:
        with op.batch_alter_table(tabla, schema=None) as batch_op:
            batch_op.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                op.f(f"fk_{tabla}_created_by_user_id_users"),
                "users",
                ["created_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index(f"ix_{tabla}_created_by_user_id", ["created_by_user_id"])


def downgrade() -> None:
    for tabla in AUDITADAS:
        with op.batch_alter_table(tabla, schema=None) as batch_op:
            batch_op.drop_index(f"ix_{tabla}_created_by_user_id")
            batch_op.drop_constraint(
                op.f(f"fk_{tabla}_created_by_user_id_users"), type_="foreignkey"
            )
            batch_op.drop_column("created_by_user_id")
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_auth_sessions_user_id")
    op.drop_table("auth_sessions")
    op.drop_table("users")
