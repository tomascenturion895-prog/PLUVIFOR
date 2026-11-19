"""Archivos maliciosos o inesperados son rechazados sin tocar la base (SCRUM-53)."""

from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import ImportMode
from app.ingestion.types import InvalidFileError, RejectionReason, UploadTooLargeError
from app.ingestion.upload import check_upload
from app.models import RainfallRecord, Station
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService

CUTOFF = date(2026, 10, 31)
HEADER = (
    "estacion_id,id_interno,nombre,tipo,localidad,provincia,lat,lon,altura_m,"
    "desde_siga,hasta_siga\n"
)
RAIN_HEADER = (
    "estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,"
    "categoria,fuente\n"
)


@pytest.fixture
def service(db: Session) -> ImportService:
    return ImportService(SqlIngestionRepository(db), CUTOFF, max_upload_bytes=2_000)


def count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_valid_csv_passes():
    check_upload("lluvia.csv", b"a,b\n1,2\n")


@pytest.mark.parametrize("name", ["datos.xlsx", "datos.csv.exe", "datos", "datos.json"])
def test_other_extensions_are_rejected(name):
    with pytest.raises(InvalidFileError, match="csv"):
        check_upload(name, b"a,b\n1,2\n")


def test_path_in_filename_does_not_change_the_check():
    check_upload("..\\..\\windows\\datos.csv", b"a,b\n1,2\n")
    with pytest.raises(InvalidFileError):
        check_upload("../../etc/passwd", b"a,b\n")


def test_empty_file_is_rejected():
    with pytest.raises(InvalidFileError, match="vacío"):
        check_upload("x.csv", b"  \n")


def test_oversized_file_is_rejected(service: ImportService):
    with pytest.raises(UploadTooLargeError, match="supera"):
        service.import_stations("siga_inta", "e.csv", b"a" * 2_001)


@pytest.mark.parametrize(
    "content",
    [b"PK\x03\x04" + b"estacion_id,nombre\n" * 3, b"%PDF-1.7\n", b"MZ\x90\x00", b"a,b\n\x00\x01\n"],
)
def test_binary_disguised_as_csv_is_rejected(content):
    with pytest.raises(InvalidFileError, match="texto"):
        check_upload("estaciones.csv", content)


def test_formula_in_station_text_is_rejected_with_reason(service: ImportService, db: Session):
    content = (
        HEADER
        + '424,A1,=HYPERLINK("http://x"),Automática,Pirané,Formosa,-26.33,-59.35,106,,\n'
        + "425,A2,@SUM(A1),Automática,Pirané,Formosa,,,,,\n"
        + "426,A3,Estación válida,Automática,Pirané,Formosa,,,,,\n"
    ).encode()
    report = service.import_stations("siga_inta", "e.csv", content)
    assert report.rows_accepted == 1
    assert report.rejections_by_reason() == {RejectionReason.TEXTO_CON_FORMULA.value: 2}
    assert count(db, Station) == 1


def test_sql_text_in_a_value_does_not_alter_the_database(service: ImportService, db: Session):
    service.import_stations(
        "siga_inta", "e.csv", (HEADER + "424,A1,El Colorado,,,Formosa,,,,,\n").encode()
    )
    malicious = (
        RAIN_HEADER
        + "424'; DROP TABLE rainfall_records;--,x,2016-01-01,1,,mm,dato,,OBSERVADO,SIGA\n"
        + "424,x,2016-01-02,1,,mm,dato,,OBSERVADO,SIGA\n"
    ).encode()
    report = service.import_rainfall("siga_inta", "l.csv", malicious, ImportMode.COMMIT)
    assert report.rejections_by_reason() == {RejectionReason.ESTACION_INEXISTENTE.value: 1}
    assert count(db, RainfallRecord) == 1  # la tabla sigue existiendo y solo entró la fila buena
    assert count(db, Station) == 1


def test_rejected_upload_is_not_recorded_as_data(service: ImportService, db: Session):
    with pytest.raises(InvalidFileError):
        service.import_rainfall("siga_inta", "l.xlsx", b"PK\x03\x04", ImportMode.COMMIT)
    assert count(db, RainfallRecord) == 0
