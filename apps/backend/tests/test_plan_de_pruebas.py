"""El plan de pruebas (docs/qa/plan-de-pruebas.md) no puede nombrar pruebas que no existen.

Cada criterio dice con qué prueba automática se verifica. Si alguien renombra o borra ese archivo,
el criterio quedaría «cubierto» solo en el papel: esta prueba lo detecta.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
PLAN = RAIZ / "docs" / "qa" / "plan-de-pruebas.md"
ARCHIVO_DE_PRUEBA = re.compile(r"`([\w.\-]+\.(?:py|tsx|ts))`")


def _pruebas_existentes() -> set[str]:
    backend = {p.name for p in (RAIZ / "apps" / "backend" / "tests").rglob("*.py")}
    frontend_dir = RAIZ / "apps" / "frontend" / "src"
    frontend = {p.name for p in frontend_dir.rglob("*.ts*")} if frontend_dir.exists() else set()
    return backend | frontend


def test_el_plan_existe_y_nombra_pruebas():
    assert PLAN.is_file(), "falta docs/qa/plan-de-pruebas.md"
    assert len(set(ARCHIVO_DE_PRUEBA.findall(PLAN.read_text(encoding="utf-8")))) >= 10


def test_toda_prueba_que_nombra_el_plan_existe():
    nombradas = set(ARCHIVO_DE_PRUEBA.findall(PLAN.read_text(encoding="utf-8")))
    faltan = sorted(nombradas - _pruebas_existentes())
    assert not faltan, f"el plan nombra pruebas que no existen: {faltan}"


@pytest.mark.parametrize("criterio", ["1.1", "3.1", "3.2", "5.1", "7.2", "9.1"])
def test_los_criterios_del_hueco_estan_marcados_con_estrella(criterio):
    """Los criterios del hueco llevan ★ y una prueba (no «Falta prueba»)."""
    lineas = PLAN.read_text(encoding="utf-8").splitlines()
    filas = [f for f in lineas if f.startswith(f"| {criterio} ")]
    assert len(filas) == 1, f"no se encontró el criterio {criterio}"
    assert "★" in filas[0]
    assert "Falta prueba" not in filas[0]
