"""Genera los datos de paridad entre la API de Go y la de Python (SCRUM-84 y SCRUM-85).

Vuelca la base de demostración a `db.json` y guarda en `cases.json` lo que responde hoy la API
de Python a una lista de consultas. Las pruebas de Go cargan `db.json` en un lector de memoria y
exigen la misma respuesta (mismo JSON, mismo código HTTP, mismo código de error).

Uso, desde apps/backend con el entorno de Python activo:

    python ../api-go/testdata/parity/generate.py

No inventa datos: todo sale de la base de demostración (reset-demo).
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[2] / "backend"

CASES = [
    # Catálogo
    "/api/stations",
    "/api/stations?limit=2&offset=1",
    "/api/stations?limit=1",
    "/api/stations?source=siga_inta",
    "/api/stations?network=INTA",
    "/api/stations?coords_status=verificada",
    "/api/stations?coords_status=pendiente",
    "/api/stations?q=colorado",
    "/api/stations?q=COLORADO",
    "/api/stations?q=zzz-no-existe",
    "/api/stations?department=Pirane&zone=Centro",
    "/api/stations/1",
    "/api/stations/2",
    "/api/stations/3",
    "/api/stations/999",
    # Serie diaria: caso feliz, hueco, recorte, advertencias
    "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-31",
    "/api/rainfall?station_id=2&from=2015-09-20&to=2016-06-26",
    "/api/rainfall?station_id=3&from=2015-09-20&to=2016-06-26",
    "/api/rainfall?station_id=1&from=2015-06-20&to=2015-07-10",
    "/api/rainfall?station_id=1&from=2020-01-01&to=2020-01-10",
    "/api/rainfall?station_id=3&from=2023-03-01&to=2023-04-10",
    "/api/rainfall?station_id=1&from=2026-10-25&to=2026-11-20",
    "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-10&category=observado",
    "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-10&category=referencia",
    "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-10&category=estimado",
    "/api/rainfall?station_id=1&from=2015-01-05&to=2015-01-05",
    # Errores de negocio
    "/api/rainfall?station_id=999&from=2015-01-01&to=2015-01-10",
    "/api/rainfall?station_id=1&from=2015-02-01&to=2015-01-01",
    "/api/rainfall?station_id=1&from=2026-11-01&to=2026-11-30",
    "/api/rainfall?station_id=1&from=2000-01-01&to=2026-10-31",
    # Entradas inválidas (422 de validación)
    "/api/stations?limit=0",
    "/api/stations?limit=201",
    "/api/stations?limit=abc",
    "/api/stations?offset=-1",
    "/api/stations?coords_status=x",
    "/api/stations?q=" + "a" * 101,
    "/api/stations?source=" + "a" * 65,
    "/api/stations/abc",
    "/api/stations/0",
    "/api/stations/99999999999999999999",
    "/api/rainfall",
    "/api/rainfall?station_id=a&from=2026-01-01&to=2026-01-05",
    "/api/rainfall?station_id=0&from=2026-01-01&to=2026-01-05",
    "/api/rainfall?station_id=99999999999999999999&from=2026-01-01&to=2026-01-05",
    "/api/rainfall?station_id=1&from=2026-13-01&to=2026-01-05",
    "/api/rainfall?station_id=1&from=2026-01-01&to=2026-01-05&category=zzz",
    "/api/rainfall?station_id=1&from=2026-01-01",
]


def dump_db(path: str) -> dict:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row

    def rows(sql: str) -> list[dict]:
        return [dict(r) for r in con.execute(sql)]

    records = [
        [r["station_id"], r["obs_date"], r["state"], r["mm"], r["category"], r["validation"]]
        for r in con.execute(
            "SELECT station_id, obs_date, state, mm, category, validation "
            "FROM rainfall_records ORDER BY station_id, category, obs_date"
        )
    ]
    return {
        "sources": rows(
            "SELECT id, code, name, network, category, day_cutoff_local FROM sources ORDER BY id"
        ),
        "stations": rows(
            "SELECT id, source_id, code, internal_code, name, kind, locality, department, zone, "
            "lat, lon, elevation_m, coords_status, active_from, active_to FROM stations ORDER BY id"
        ),
        "flags": rows(
            "SELECT station_id, code, start_date, end_date, severity FROM quality_flags "
            "ORDER BY station_id, start_date"
        ),
        "records_columns": ["station_id", "obs_date", "state", "mm", "category", "validation"],
        "records": records,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "parity.db")
        env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}", "DATA_CUTOFF_DATE": "2026-10-31"}
        subprocess.run(
            [sys.executable, "-m", "app.cli", "reset-demo", "--yes"],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
        )
        os.environ.update(env)
        sys.path.insert(0, str(BACKEND))
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        cases = []
        for path in CASES:
            r = client.get(path)
            cases.append({"path": path, "status": r.status_code, "body": r.json()})
        data = dump_db(db)

    (HERE / "db.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (HERE / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, separators=(",", ":")))
    print(f"db.json: {len(data['records'])} días · cases.json: {len(cases)} consultas")


if __name__ == "__main__":
    main()
