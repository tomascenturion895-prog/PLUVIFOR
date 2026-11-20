"""Relaciones entre tablas: toda clave foránea tiene índice, y se borra o se protege a propósito."""

from datetime import date

import pytest
from sqlalchemy import Table, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.domain.alerts import Channel, MessageKind
from app.domain.enums import DataCategory, RainState, Validation
from app.models import (
    AlertOutbox,
    AlertSubscription,
    AlertSubscriptionStation,
    RainfallRecord,
    Source,
    Station,
)


def _columnas_cubiertas(tabla: Table) -> list[list[str]]:
    """Listas de columnas que arrancan un índice, una restricción única o la clave primaria."""
    cubiertas = [[c.name for c in tabla.primary_key.columns]]
    cubiertas += [[c.name for c in i.columns] for i in tabla.indexes]
    cubiertas += [
        [c.name for c in u.columns]
        for u in tabla.constraints
        if u.__class__.__name__ == "UniqueConstraint"
    ]
    return cubiertas


def test_toda_clave_foranea_tiene_un_indice_que_empieza_por_ella():
    sin_indice = []
    for tabla in Base.metadata.sorted_tables:
        cubiertas = _columnas_cubiertas(tabla)
        for fk in tabla.foreign_key_constraints:
            columnas = [c.name for c in fk.columns]
            if not any(cub[: len(columnas)] == columnas for cub in cubiertas):
                sin_indice.append(f"{tabla.name}.{columnas}")
    assert sin_indice == [], f"claves foráneas sin índice: {sin_indice}"


def _fuente_y_estacion(db: Session) -> Station:
    fuente = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    db.add(fuente)
    db.flush()
    estacion = Station(source_id=fuente.id, code="424", name="El Colorado")
    db.add(estacion)
    db.flush()
    return estacion


def test_los_mensajes_de_una_suscripcion_se_borran_con_ella(db: Session):
    uno = AlertSubscription(phone_hash="a" * 64, phone_last4="3456")
    otro = AlertSubscription(phone_hash="b" * 64, phone_last4="9999")
    db.add_all([uno, otro])
    db.flush()
    for sub in (uno, uno, otro):
        db.add(
            AlertOutbox(
                subscription_id=sub.id, kind=MessageKind.CODIGO, channel=Channel.WHATSAPP, body="x"
            )
        )
    db.commit()
    db.execute(delete(AlertSubscription).where(AlertSubscription.id == uno.id))
    db.commit()
    restantes = db.scalars(select(AlertOutbox)).all()
    assert [m.subscription_id for m in restantes] == [otro.id]


def test_un_mensaje_no_puede_apuntar_a_una_suscripcion_que_no_existe(db: Session):
    db.add(
        AlertOutbox(
            subscription_id=9999, kind=MessageKind.CODIGO, channel=Channel.WHATSAPP, body="x"
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_no_se_puede_borrar_una_estacion_que_tiene_lluvia_registrada(db: Session):
    """Los datos medidos nunca se borran en cascada: primero hay que decidirlo a propósito."""
    estacion = _fuente_y_estacion(db)
    db.add(
        RainfallRecord(
            station_id=estacion.id,
            obs_date=date(2016, 1, 1),
            state=RainState.DATO,
            mm=12.5,
            category=DataCategory.OBSERVADO,
            validation=Validation.SIN_VALIDAR,
        )
    )
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(delete(Station).where(Station.id == estacion.id))
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(RainfallRecord)) == 1


def test_una_suscripcion_no_puede_pedir_una_estacion_que_no_existe(db: Session):
    db.add(AlertSubscriptionStation(subscription_id=9999, station_id=9999))
    with pytest.raises(IntegrityError):
        db.commit()


def test_borrar_una_suscripcion_borra_sus_estaciones_pero_no_las_estaciones(db: Session):
    estacion = _fuente_y_estacion(db)
    sub = AlertSubscription(phone_hash="d" * 64, phone_last4="2222")
    db.add(sub)
    db.flush()
    db.add(AlertSubscriptionStation(subscription_id=sub.id, station_id=estacion.id))
    db.commit()
    db.execute(delete(AlertSubscription).where(AlertSubscription.id == sub.id))
    db.commit()
    assert db.scalar(select(func.count()).select_from(AlertSubscriptionStation)) == 0
    assert db.get(Station, estacion.id) is not None


def test_no_se_puede_borrar_una_estacion_que_tiene_suscriptores(db: Session):
    estacion = _fuente_y_estacion(db)
    sub = AlertSubscription(phone_hash="e" * 64, phone_last4="3333")
    db.add(sub)
    db.flush()
    db.add(AlertSubscriptionStation(subscription_id=sub.id, station_id=estacion.id))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(delete(Station).where(Station.id == estacion.id))
        db.commit()
    db.rollback()


def test_una_suscripcion_no_repite_la_misma_estacion(db: Session):
    estacion = _fuente_y_estacion(db)
    sub = AlertSubscription(phone_hash="f" * 64, phone_last4="4444")
    db.add(sub)
    db.flush()
    db.add(AlertSubscriptionStation(subscription_id=sub.id, station_id=estacion.id))
    db.commit()
    db.add(AlertSubscriptionStation(subscription_id=sub.id, station_id=estacion.id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
