"""Reinicio de la base de demo (SCRUM-45)."""

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app import cli
from app.demo import DemoResetError, reset_demo, sqlite_file
from app.models import QualityFlag, RainfallRecord, Station

CUTOFF = date(2026, 10, 31)
SI = lambda _: True  # noqa: E731
NO = lambda _: False  # noqa: E731


def contar(url: str) -> tuple[int, int, int]:
    engine = create_engine(url)
    with Session(engine) as db:
        datos = tuple(
            db.scalar(select(func.count()).select_from(m))
            for m in (Station, RainfallRecord, QualityFlag)
        )
    engine.dispose()
    return datos


@pytest.fixture
def url(tmp_path) -> str:
    return f"sqlite:///{tmp_path / 'demo.db'}"


def test_desde_cero_deja_la_demo_cargada_con_la_advertencia(url):
    result = reset_demo(url, CUTOFF, SI)
    assert result is not None
    assert (result.stations, result.rainfall_rows, result.rejected_rows) == (3, 7648, 0)
    assert result.zero_streaks == 1
    assert contar(url) == (3, 7648, 1)


def test_correrlo_dos_veces_da_el_mismo_estado(url):
    reset_demo(url, CUTOFF, SI)
    primero = contar(url)
    reset_demo(url, CUTOFF, SI)
    assert contar(url) == primero


def test_borra_lo_que_hubiera_antes(url):
    reset_demo(url, CUTOFF, SI)
    engine = create_engine(url)
    with Session(engine) as db:
        db.add(Station(source_id=1, code="999", name="Sobrante"))
        db.commit()
    engine.dispose()
    reset_demo(url, CUTOFF, SI)
    assert contar(url)[0] == 3


def test_si_no_se_confirma_no_se_toca_la_base(url, tmp_path):
    reset_demo(url, CUTOFF, SI)
    antes = (tmp_path / "demo.db").read_bytes()
    assert reset_demo(url, CUTOFF, NO) is None
    assert (tmp_path / "demo.db").read_bytes() == antes


def test_pide_confirmacion_indicando_que_archivo_se_borra(url, tmp_path):
    vistos: list[Path] = []
    reset_demo(url, CUTOFF, lambda p: vistos.append(p) or True)
    assert vistos == [(tmp_path / "demo.db").resolve()]


def test_si_faltan_los_datos_no_se_borra_nada(url, tmp_path):
    reset_demo(url, CUTOFF, SI)
    antes = contar(url)
    with pytest.raises(DemoResetError, match="No se borró nada"):
        reset_demo(url, CUTOFF, SI, data_dir=tmp_path / "vacio")
    assert contar(url) == antes


@pytest.mark.parametrize(
    "otra", ["postgresql+psycopg://u:p@host/db", "sqlite://", "sqlite:///:memory:"]
)
def test_rechaza_bases_que_no_son_un_archivo_sqlite(otra):
    with pytest.raises(DemoResetError):
        sqlite_file(otra)


def test_no_toca_una_base_de_otro_motor():
    with pytest.raises(DemoResetError, match="solo funciona con una base SQLite"):
        reset_demo("postgresql+psycopg://u:p@host/db", CUTOFF, SI)


def test_el_mensaje_de_error_no_muestra_la_clave_de_la_base():
    with pytest.raises(DemoResetError) as error:
        sqlite_file("postgresql+psycopg://usuario:clave-secreta@host/db")
    assert "clave-secreta" not in str(error.value)


def test_el_comando_sin_terminal_ni_yes_no_borra(monkeypatch, url, tmp_path, capsys):
    monkeypatch.setenv("DATABASE_URL", url)
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert cli.main(["reset-demo"]) == 1
        assert "--yes" in capsys.readouterr().err
        assert not (tmp_path / "demo.db").exists()
        assert cli.main(["reset-demo", "--yes"]) == 0
        assert "Base reiniciada" in capsys.readouterr().out
        assert contar(url)[1] == 7648
    finally:
        get_settings.cache_clear()
