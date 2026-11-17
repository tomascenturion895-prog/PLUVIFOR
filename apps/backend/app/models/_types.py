"""Tipos de columna compartidos."""

from enum import StrEnum

from sqlalchemy import Enum


def text_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """Enum guardado como texto con CHECK: igual en SQLite y PostgreSQL (sin tipos nativos)."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda cls: [member.value for member in cls],
        length=32,
    )
