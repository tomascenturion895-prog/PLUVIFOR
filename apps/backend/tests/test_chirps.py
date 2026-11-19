"""Tests para el conector de CHIRPS v3 (SCRUM-43)."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, ImportMode
from app.ingestion.chirps import ChirpsCsvConnector
from app.ingestion.types import InvalidFileError
from app.models import ImportLog, RainfallRecord, Source, Station
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService

CUTOFF = date(2026, 10, 31)

CHIRPS_HEADER = "estacion_id,fecha,mm,unidad,estado,categoria,fuente\n"


def test_chirps_connector_reads_estimated_rainfall():
    connector = ChirpsCsvConnector()
    assert connector.definition.code == "chirps_v3"
    assert connector.definition.category == DataCategory.ESTIMADO

    csv_data = (
        CHIRPS_HEADER
        + "424,2016-01-01,15.2,mm,dato,estimado,CHIRPS v3\n"
        + "424,2016-01-02,,mm,sin_fila,estimado,CHIRPS v3\n"
    )
    rows = list(connector.read_rainfall(csv_data))
    assert len(rows) == 2
    assert rows[0].station_code == "424"
    assert rows[0].obs_date == "2016-01-01"
    assert rows[0].mm == "15.2"
    assert rows[0].category == "estimado"
    assert rows[1].state == "sin_fila"
    assert rows[1].mm == ""


def test_chirps_connector_missing_column_raises_error():
    connector = ChirpsCsvConnector()
    bad_csv = "estacion_id,fecha,mm\n424,2016-01-01,10.0\n"
    with pytest.raises(InvalidFileError, match="Faltan columnas"):
        list(connector.read_rainfall(bad_csv))


def test_import_chirps_records_as_estimated_and_never_mix_with_observed(db: Session):
    # Crear estación y fuente observada
    siga = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
    )
    db.add(siga)
    db.flush()
    station = Station(source_id=siga.id, code="424", name="El Colorado")
    db.add(station)
    db.commit()

    # Importar fila observada
    db.add(
        RainfallRecord(
            station_id=station.id,
            obs_date=date(2016, 1, 1),
            state="dato",
            mm=20.0,
            category=DataCategory.OBSERVADO,
        )
    )
    db.commit()

    service = ImportService(SqlIngestionRepository(db), CUTOFF)
    chirps_csv = (
        CHIRPS_HEADER
        + "424,2016-01-01,12.4,mm,dato,estimado,CHIRPS v3\n"
        + "424,2016-01-02,,mm,fila_sin_valor,estimado,CHIRPS v3\n"
    ).encode()

    # Import commit
    report = service.import_rainfall(
        "chirps_v3", "chirps_424_demo.csv", chirps_csv, mode=ImportMode.COMMIT
    )
    assert report.rows_read == 2
    assert report.rows_accepted == 2
    assert report.inserted == 2

    # Verificar que se creó la fuente chirps_v3 en la BD
    chirps_source = db.scalar(select(Source).where(Source.code == "chirps_v3"))
    assert chirps_source is not None
    assert chirps_source.category == DataCategory.ESTIMADO

    # Verificar registros en rainfall_records
    records = list(
        db.scalars(
            select(RainfallRecord)
            .where(RainfallRecord.station_id == station.id)
            .order_by(RainfallRecord.category, RainfallRecord.obs_date)
        )
    )
    # 1 observado + 2 estimados
    assert len(records) == 3

    obs_records = [r for r in records if r.category == DataCategory.OBSERVADO]
    est_records = [r for r in records if r.category == DataCategory.ESTIMADO]

    assert len(obs_records) == 1
    assert obs_records[0].mm == 20.0

    assert len(est_records) == 2
    assert est_records[0].mm == 12.4
    assert est_records[0].obs_date == date(2016, 1, 1)
    # Hueco no es 0 mm
    assert est_records[1].mm is None
    assert est_records[1].state.value == "fila_sin_valor"

    # Verificar registro en import_logs
    log = db.scalar(select(ImportLog).where(ImportLog.filename == "chirps_424_demo.csv"))
    assert log is not None
    assert log.source_id == chirps_source.id
    assert log.rows_read == 2
