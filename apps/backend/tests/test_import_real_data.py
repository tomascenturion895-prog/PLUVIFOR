"""Carga real de las series del SIGA: los conteos tienen que coincidir con docs/modelo-datos.md."""

from collections import Counter
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import ImportMode
from app.models import RainfallRecord
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService

DATA = Path(__file__).resolve().parents[3] / "docs" / "datos"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="docs/datos no está disponible")


def test_siga_series_load_with_expected_counts(db: Session) -> None:
    service = ImportService(SqlIngestionRepository(db), date(2026, 10, 31))
    stations = service.import_stations(
        "siga_inta", "e.csv", (DATA / "estaciones_siga_formosa.csv").read_bytes()
    )
    assert stations.rows_accepted == 3 and stations.rows_rejected == 0

    report = service.import_rainfall(
        "siga_inta",
        "l.csv",
        (DATA / "lluvia_diaria_siga_formosa.csv").read_bytes(),
        ImportMode.COMMIT,
    )
    assert report.rows_read == 7648 and report.rows_rejected == 0

    states = Counter(r.state.value for r in db.scalars(select(RainfallRecord)))
    assert states == {"dato": 5265, "fila_sin_valor": 365, "sin_fila": 2018}
    # Ningún hueco quedó guardado como cero.
    gaps_with_mm = [
        r
        for r in db.scalars(select(RainfallRecord))
        if r.state.value != "dato" and r.mm is not None
    ]
    assert gaps_with_mm == []
