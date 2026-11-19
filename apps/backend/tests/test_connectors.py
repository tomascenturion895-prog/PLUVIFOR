"""Un conector nuevo se suma sin tocar el resto de la importación (SCRUM-47)."""

from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, ImportMode
from app.ingestion.registry import DEFAULT_CONNECTORS, build_registry
from app.ingestion.siga import SigaCsvConnector
from app.ingestion.sources import SourceDefinition
from app.ingestion.types import (
    InvalidFileError,
    RawRainRow,
    Rejection,
    RejectionReason,
    StationRow,
)
from app.models import RainfallRecord, Source
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService

CUTOFF = date(2026, 10, 31)

SIGA_RAIN = (
    "estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,"
    "categoria,fuente\n"
    "424,x,2016-01-01,12.5,,mm,dato,,OBSERVADO,SIGA INTA\n"
    "424,x,2016-01-02,-3,,mm,dato,,OBSERVADO,SIGA INTA\n"
)
SIGA_STATIONS = (
    "estacion_id,id_interno,nombre,tipo,localidad,provincia,lat,lon,altura_m,desde_siga,hasta_siga\n"
    "424,A1,El Colorado,Automática,Pirané,Formosa,-26.33,-59.35,106,2013-10-07,2022-12-07\n"
)


class FakeConnector:
    """Fuente inventada para la prueba: usa «;» y una sola columna de lluvia."""

    definition = SourceDefinition(
        code="fuente_falsa",
        name="Fuente falsa de prueba",
        network="PRUEBA",
        category=DataCategory.REFERENCIA,
        day_cutoff_local="09:00",
    )

    def read_stations(self, text: str) -> tuple[list[StationRow], list[Rejection]]:
        rows = []
        for line in text.strip().splitlines()[1:]:
            code, name = line.split(";")
            rows.append(StationRow(code, None, name, None, None, None, None, None, None, None))
        return rows, []

    def read_rainfall(self, text: str) -> Iterator[RawRainRow]:
        for number, line in enumerate(text.strip().splitlines()[1:], start=2):
            code, day, mm = line.split(";")
            yield RawRainRow(number, code, day, mm, "", "mm", "dato", "referencia")


@pytest.fixture
def service(db: Session) -> ImportService:
    connectors = build_registry([SigaCsvConnector(), FakeConnector()])
    return ImportService(SqlIngestionRepository(db), CUTOFF, connectors=connectors)


def test_siga_connector_declares_source_category_and_cutoff_field():
    definition = SigaCsvConnector().definition
    assert definition.code == "siga_inta"
    assert definition.category is DataCategory.OBSERVADO
    assert hasattr(definition, "day_cutoff_local")


def test_default_registry_has_the_siga_connector():
    assert "siga_inta" in DEFAULT_CONNECTORS


def test_siga_csv_one_valid_row_and_one_invalid(service: ImportService):
    service.import_stations("siga_inta", "estaciones.csv", SIGA_STATIONS.encode())
    report = service.import_rainfall(
        "siga_inta", "lluvia.csv", SIGA_RAIN.encode(), ImportMode.AUDIT
    )
    assert (report.rows_read, report.rows_accepted, report.rows_rejected) == (2, 1, 1)
    assert report.rejections[0].reason is RejectionReason.MM_NEGATIVO


def test_a_new_connector_is_added_without_changing_the_others(service: ImportService, db: Session):
    service.import_stations("siga_inta", "estaciones.csv", SIGA_STATIONS.encode())
    service.import_stations("fuente_falsa", "e.csv", b"codigo;nombre\nZ1;Estacion Z\n")
    report = service.import_rainfall(
        "fuente_falsa", "l.csv", b"codigo;dia;mm\nZ1;2016-03-01;4.0\n", ImportMode.COMMIT
    )
    assert report.inserted == 1
    stored = db.scalars(select(RainfallRecord)).all()
    assert len(stored) == 1 and stored[0].category is DataCategory.REFERENCIA
    assert {s.code for s in db.scalars(select(Source)).all()} == {"siga_inta", "fuente_falsa"}
    # La fuente original sigue funcionando igual.
    again = service.import_rainfall("siga_inta", "lluvia.csv", SIGA_RAIN.encode(), ImportMode.AUDIT)
    assert again.rows_accepted == 1


def test_unknown_source_is_rejected(service: ImportService):
    with pytest.raises(InvalidFileError, match="desconocida"):
        service.import_rainfall("no_existe", "x.csv", b"", ImportMode.AUDIT)
    with pytest.raises(InvalidFileError, match="desconocida"):
        service.import_stations("no_existe", "x.csv", b"")


def test_repeated_source_code_in_registry_is_an_error():
    with pytest.raises(ValueError, match="repetida"):
        build_registry([SigaCsvConnector(), SigaCsvConnector()])
