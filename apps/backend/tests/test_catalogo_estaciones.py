"""Catálogo de estaciones del prototipo (SCRUM-31): reales, candidatas y simuladas separadas."""

import csv
import importlib.util
from collections import Counter
from pathlib import Path

import pytest

from app.ingestion.siga import SigaCsvConnector
from app.ingestion.types import InvalidFileError

RAIZ = Path(__file__).resolve().parents[3]
DATOS = RAIZ / "docs" / "datos"


def _cargar_script():
    spec = importlib.util.spec_from_file_location(
        "generar_estaciones", DATOS / "generar_estaciones.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def filas() -> list[dict]:
    with (DATOS / "estaciones.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_el_catalogo_tiene_3_reales_15_candidatas_y_34_simuladas(filas) -> None:
    assert Counter(f["estado_catalogo"] for f in filas) == {
        "real_cargada": 3,
        "candidata_licencia_pendiente": 15,
        "simulada": 34,
    }


def test_los_codigos_no_se_repiten(filas) -> None:
    codigos = [f["codigo"] for f in filas]
    assert len(codigos) == len(set(codigos))


def test_las_simuladas_nunca_figuran_como_observadas_ni_verificadas(filas) -> None:
    simuladas = [f for f in filas if f["estado_catalogo"] == "simulada"]
    for f in simuladas:
        assert f["categoria"] == "simulado"
        assert f["coords_status"] == "simulada"
        assert "simulada" in f["nombre"].lower()
        assert "no es una estación real" in f["nota"]
        assert f["altura_m"] == ""  # no se inventa la altura
    assert not [
        f for f in filas if f["estado_catalogo"] != "simulada" and f["categoria"] == "simulado"
    ]


def test_las_reales_coinciden_con_el_original_del_siga(filas) -> None:
    with (DATOS / "estaciones_siga_formosa.csv").open(encoding="utf-8", newline="") as f:
        originales = {r["estacion_id"]: r for r in csv.DictReader(f)}
    reales = {f["codigo"]: f for f in filas if f["estado_catalogo"] == "real_cargada"}
    assert set(reales) == {f"siga_{k}" for k in originales}
    for codigo, f in reales.items():
        origen = originales[codigo.removeprefix("siga_")]
        assert (f["lat"], f["lon"], f["nombre"]) == (origen["lat"], origen["lon"], origen["nombre"])


def test_las_candidatas_del_ina_avisan_que_falta_la_licencia(filas) -> None:
    ina = [f for f in filas if f["estado_catalogo"] == "candidata_licencia_pendiente"]
    assert all("Licencia sin confirmar" in f["nota"] for f in ina)
    # Las que están sobre el límite provincial quedan con coordenadas pendientes, no verificadas.
    limite = [f for f in ina if "límite provincial" in f["nota"]]
    assert limite and all(f["coords_status"] == "pendiente" for f in limite)


def test_las_simuladas_estan_dentro_de_la_provincia(filas) -> None:
    script = _cargar_script()
    contorno, _ = script._cargar_geo()
    for f in filas:
        if f["estado_catalogo"] == "simulada":
            assert script._en(contorno, float(f["lon"]), float(f["lat"])), f["codigo"]


def test_el_archivo_se_puede_regenerar_igual() -> None:
    script = _cargar_script()
    esperado = script.generar()
    with (DATOS / "estaciones.csv").open(encoding="utf-8", newline="") as f:
        guardado = list(csv.DictReader(f))
    assert guardado == [{k: str(v) for k, v in fila.items()} for fila in esperado]


def test_el_importador_del_siga_rechaza_este_catalogo() -> None:
    """Entrada inválida: no se puede cargar por error como si todo fuera del SIGA."""
    texto = (DATOS / "estaciones.csv").read_text(encoding="utf-8")
    with pytest.raises(InvalidFileError):
        SigaCsvConnector().read_stations(texto)
