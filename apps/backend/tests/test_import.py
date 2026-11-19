from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, ImportMode, RainState
from app.ingestion.types import InvalidFileError, RawRainRow, RejectionReason
from app.ingestion.validation import RowValidator
from app.models import ImportLog, RainfallRecord, Station
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService

CUTOFF = date(2026, 10, 31)
STATIONS = (
    "estacion_id,id_interno,nombre,tipo,localidad,provincia,lat,lon,altura_m,desde_siga,hasta_siga\n"
    "424,A1,El Colorado,Automática,Pirané,Formosa,-26.33,-59.35,106,2013-10-07,2022-12-07\n"
    "425,A2,Bartolomé,Automática,BDLC,Formosa,,,,,\n"
)
HEADER = (
    "estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,"
    "categoria,fuente\n"
)


def rain(*lines: str) -> bytes:
    return (HEADER + "\n".join(lines) + "\n").encode()


def line(code="424", day="2016-01-01", mm="0", chrono="", unit="mm", state="dato", cat="OBSERVADO"):
    return f"{code},x,{day},{mm},{chrono},{unit},{state},,{cat},SIGA INTA"


@pytest.fixture
def service(db: Session) -> ImportService:
    svc = ImportService(SqlIngestionRepository(db), CUTOFF)
    svc.import_stations("siga_inta", "estaciones.csv", STATIONS.encode())
    return svc


def raw(**overrides) -> RawRainRow:
    base = {
        "line": 2,
        "station_code": "424",
        "obs_date": "2016-01-01",
        "mm": "0",
        "mm_chrono": "",
        "unit": "mm",
        "state": "dato",
        "category": "OBSERVADO",
    }
    return RawRainRow(**{**base, **overrides})


def validator() -> RowValidator:
    return RowValidator(CUTOFF, {"424"})


def test_zero_is_valid_data():
    assert validator().validate(raw(mm="0")).mm == 0.0


@pytest.mark.parametrize("state", ["sin_fila", "fila_sin_valor"])
def test_gap_without_value_is_kept_as_none(state):
    row = validator().validate(raw(mm="", state=state))
    assert row.mm is None and row.state.value == state


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"station_code": "999"}, RejectionReason.ESTACION_INEXISTENTE),
        ({"obs_date": "2016-13-45"}, RejectionReason.FECHA_INVALIDA),
        ({"obs_date": "2026-11-01"}, RejectionReason.FECHA_POSTERIOR_AL_CORTE),
        ({"mm": "-3"}, RejectionReason.MM_NEGATIVO),
        ({"mm": "abc"}, RejectionReason.MM_INVALIDO),
        ({"mm": "nan"}, RejectionReason.MM_INVALIDO),
        ({"state": "dato", "mm": ""}, RejectionReason.ESTADO_INCOHERENTE),
        ({"state": "sin_fila", "mm": "0"}, RejectionReason.ESTADO_INCOHERENTE),
        ({"state": "raro"}, RejectionReason.ESTADO_INVALIDO),
        ({"category": "inventada"}, RejectionReason.CATEGORIA_INVALIDA),
        ({"unit": "in"}, RejectionReason.UNIDAD_INVALIDA),
    ],
)
def test_invalid_rows_are_rejected_with_reason(overrides, reason):
    assert validator().validate(raw(**overrides)) == reason


def test_duplicate_in_file_is_rejected():
    v = validator()
    v.validate(raw())
    assert v.validate(raw()) == RejectionReason.DUPLICADO_EN_ARCHIVO


def test_audit_does_not_write_rainfall(service: ImportService, db: Session):
    report = service.import_rainfall("siga_inta", "l.csv", rain(line()), ImportMode.AUDIT)
    assert report.rows_accepted == 1 and report.inserted == 0
    assert db.scalar(select(func.count()).select_from(RainfallRecord)) == 0
    assert db.scalar(select(ImportLog.mode)).value == "audit"


def test_commit_saves_and_keeps_gaps_as_gaps(service: ImportService, db: Session):
    content = rain(
        line(day="2016-01-01", mm="0"),
        line(day="2016-01-02", mm="", state="sin_fila"),
        line(day="2016-01-03", mm="", chrono="2.5", state="fila_sin_valor"),
    )
    report = service.import_rainfall("siga_inta", "l.csv", content, ImportMode.COMMIT)
    assert (report.inserted, report.updated) == (3, 0)
    records = {r.obs_date: r for r in db.scalars(select(RainfallRecord))}
    assert records[date(2016, 1, 1)].mm == 0.0
    assert records[date(2016, 1, 2)].mm is None
    assert records[date(2016, 1, 3)].mm is None and records[date(2016, 1, 3)].mm_chrono == 2.5
    assert records[date(2016, 1, 3)].category == DataCategory.OBSERVADO
    assert records[date(2016, 1, 3)].state == RainState.FILA_SIN_VALOR


def test_reimport_is_idempotent(service: ImportService, db: Session):
    content = rain(line(day="2016-01-01", mm="5"), line(day="2016-01-02", mm="0"))
    service.import_rainfall("siga_inta", "l.csv", content, ImportMode.COMMIT)
    again = service.import_rainfall("siga_inta", "l.csv", content, ImportMode.COMMIT)
    assert (again.inserted, again.updated) == (0, 2)
    assert db.scalar(select(func.count()).select_from(RainfallRecord)) == 2


def test_rejections_are_logged_with_reason(service: ImportService, db: Session):
    content = rain(line(), line(day="2027-01-01"), line(mm="-1", day="2016-01-05"))
    report = service.import_rainfall("siga_inta", "../../etc/l.csv", content, ImportMode.COMMIT)
    assert report.rows_rejected == 2 and report.filename == "l.csv"
    log = db.scalar(select(ImportLog).order_by(ImportLog.id.desc()))
    assert log.rows_read == 3 and log.rows_accepted == 1 and log.rows_rejected == 2
    assert "fecha_posterior_al_corte" in log.rejections and len(log.sha256) == 64
    assert db.scalar(select(func.count()).select_from(RainfallRecord)) == 1


def test_station_catalog_keeps_missing_coordinates_empty(service: ImportService, db: Session):
    stations = {s.code: s for s in db.scalars(select(Station))}
    assert stations["425"].lat is None and stations["425"].coords_status.value == "pendiente"
    assert stations["424"].coords_status.value == "verificada"


def test_catalog_with_invalid_coordinates_is_rejected(db: Session):
    svc = ImportService(SqlIngestionRepository(db), CUTOFF)
    bad = (
        STATIONS + "426,A3,Mala,Auto,X,Formosa,-200,-59,1,,\n427,A4,Media,Auto,X,Formosa,-26,,1,,\n"
    )
    report = svc.import_stations("siga_inta", "e.csv", bad.encode())
    assert report.rows_rejected == 2 and report.inserted == 2


def test_unknown_source_and_bad_files_fail_cleanly(service: ImportService):
    with pytest.raises(InvalidFileError):
        service.import_rainfall("nada", "x.csv", rain(line()), ImportMode.AUDIT)
    with pytest.raises(InvalidFileError):
        service.import_rainfall("siga_inta", "x.csv", b"col1,col2\n1,2\n", ImportMode.AUDIT)
    with pytest.raises(InvalidFileError):
        service.import_rainfall("siga_inta", "x.csv", b"\xff\xfe\x00", ImportMode.AUDIT)
    with pytest.raises(InvalidFileError):
        service.import_stations("nada", "x.csv", STATIONS.encode())
