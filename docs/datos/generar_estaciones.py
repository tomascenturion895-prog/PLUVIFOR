"""Arma docs/datos/estaciones.csv: el catálogo de estaciones del prototipo (SCRUM-31).

Une tres grupos, siempre con su estado a la vista:
  - real_cargada: las 3 estaciones del SIGA/INTA (docs/datos/estaciones_siga_formosa.csv).
  - candidata_licencia_pendiente: las 15 estaciones del INA (docs/datos/ina_estaciones_formosa.csv).
    No se cargan en la base hasta confirmar su licencia y que sus series existan.
  - simulada: 34 estaciones de EJEMPLO que ocupan el lugar de las 34 provinciales, cuya lista
    todavía no entregó la mentoría. NO son estaciones reales.

Cómo se ubican las simuladas (reproducible, sin azar): se recorre una grilla de 0,05° dentro
del contorno de la provincia (capa del IGN del repositorio) y se elige, de a una, el punto más
alejado de todas las estaciones ya existentes. Así rellenan los huecos de la red real y sirven
para mostrar el mapa y la regla de estaciones vecinas. El departamento sale de la capa del IGN.

Uso (desde la raíz del repositorio):  python docs/datos/generar_estaciones.py
Solo usa la biblioteca estándar.
"""

import csv
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "docs" / "datos"
GEO = RAIZ / "apps" / "frontend" / "public" / "geo"
SALIDA = DATOS / "estaciones.csv"
CANTIDAD_SIMULADAS = 34
PASO_GRILLA = 0.05  # grados (~5 km)
MARGEN = 0.15  # grados: no se ponen estaciones simuladas pegadas al borde

COLUMNAS = [
    "codigo", "id_interno", "nombre", "tipo", "localidad", "departamento", "provincia",
    "lat", "lon", "altura_m", "coords_status", "activa_desde", "activa_hasta",
    "fuente", "categoria", "estado_catalogo", "nota",
]  # fmt: skip

NOTA_SIMULADA = (
    "EJEMPLO ilustrativo: no es una estación real. Ocupa el lugar de las 34 provinciales hasta "
    "tener la lista oficial. Posición generada por el script, sin datos de lluvia."
)


def _anillos(geometry: dict) -> list[list[list[float]]]:
    polys = (
        geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    )
    return [poly[0] for poly in polys]  # solo el contorno exterior de cada polígono


def _dentro(lon: float, lat: float, anillo: list[list[float]]) -> bool:
    adentro = False
    j = len(anillo) - 1
    for i in range(len(anillo)):
        xi, yi = anillo[i][0], anillo[i][1]
        xj, yj = anillo[j][0], anillo[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            adentro = not adentro
        j = i
    return adentro


def _en(anillos: list[list[list[float]]], lon: float, lat: float) -> bool:
    return any(_dentro(lon, lat, a) for a in anillos)


def _cargar_geo() -> tuple[list, list[tuple[str, list]]]:
    provincia = json.loads((GEO / "formosa_provincia.geojson").read_text(encoding="utf-8"))
    deptos = json.loads((GEO / "formosa_departamentos.geojson").read_text(encoding="utf-8"))
    contorno = _anillos(provincia["features"][0]["geometry"])
    por_depto = [(f["properties"]["nombre"], _anillos(f["geometry"])) for f in deptos["features"]]
    return contorno, por_depto


def _departamento(por_depto: list[tuple[str, list]], lon: float, lat: float) -> str:
    for nombre, anillos in por_depto:
        if _en(anillos, lon, lat):
            return nombre
    return ""  # sobre el límite o fuera de la capa: queda vacío, no se adivina


def _distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dy = (lat1 - lat2) * 111.0
    dx = (lon1 - lon2) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


def _reales() -> list[dict]:
    filas: list[dict] = []
    with (DATOS / "estaciones_siga_formosa.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            filas.append({
                "codigo": f"siga_{r['estacion_id']}", "id_interno": r["id_interno"],
                "nombre": r["nombre"], "tipo": r["tipo"], "localidad": r["localidad"],
                "provincia": r["provincia"], "lat": r["lat"], "lon": r["lon"],
                "altura_m": r["altura_m"], "coords_status": "verificada",
                "activa_desde": r["desde_siga"], "activa_hasta": r["hasta_siga"],
                "fuente": "SIGA INTA", "categoria": "observado",
                "estado_catalogo": "real_cargada", "nota": "",
            })  # fmt: skip
    with (DATOS / "ina_estaciones_formosa.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            limite = "límite provincial" in r["ubicacion"]
            filas.append({
                "codigo": f"ina_{r['p_diaria_serie_id']}", "id_interno": "",
                "nombre": r["nombre"].strip(), "tipo": "Red INA", "localidad": "",
                "provincia": "Formosa", "lat": r["lat"], "lon": r["lon"], "altura_m": "",
                "coords_status": "pendiente" if limite else "verificada",
                "activa_desde": r["p_diaria_desde"], "activa_hasta": r["p_diaria_hasta"],
                "fuente": "INA (alerta.ina.gob.ar)", "categoria": "observado",
                "estado_catalogo": "candidata_licencia_pendiente",
                "nota": "Licencia sin confirmar; el informe SCRUM-27 no encontró lluvia diaria "
                + "usable. "
                + ("Ubicación sobre el límite provincial: verificar. " if limite else "")
                + "Las fechas son de la serie de lluvia diaria que publica el INA.",
            })  # fmt: skip
    return filas


def _simuladas(
    contorno: list, por_depto: list, existentes: list[tuple[float, float]]
) -> list[dict]:
    candidatos: list[tuple[float, float]] = []
    lat = -27.0
    while lat <= -22.0:
        lon = -62.5
        while lon <= -57.0:
            la, lo = round(lat, 4), round(lon, 4)
            vecinos = [(la + dy, lo + dx) for dy in (-MARGEN, MARGEN) for dx in (-MARGEN, MARGEN)]
            if _en(contorno, lo, la) and all(_en(contorno, vo, va) for va, vo in vecinos):
                candidatos.append((la, lo))
            lon += PASO_GRILLA
        lat += PASO_GRILLA

    puestas = list(existentes)
    elegidas: list[tuple[float, float]] = []
    for _ in range(CANTIDAD_SIMULADAS):
        mejor = max(
            candidatos,
            key=lambda c: (min(_distancia_km(c[0], c[1], p[0], p[1]) for p in puestas), c[0], c[1]),
        )
        elegidas.append(mejor)
        puestas.append(mejor)

    # Orden de lectura: de norte a sur y de oeste a este, para numerarlas de forma estable.
    elegidas.sort(key=lambda c: (-c[0], c[1]))
    filas = []
    for n, (la, lo) in enumerate(elegidas, start=1):
        depto = _departamento(por_depto, lo, la)
        filas.append({
            "codigo": f"sim_{n:02d}", "id_interno": "",
            "nombre": f"Estación simulada {n:02d}" + (f" · Dpto. {depto}" if depto else ""),
            "tipo": "Simulada (ejemplo)", "localidad": "", "departamento": depto,
            "provincia": "Formosa", "lat": f"{la:.4f}", "lon": f"{lo:.4f}", "altura_m": "",
            "coords_status": "simulada", "activa_desde": "", "activa_hasta": "",
            "fuente": "Simulado · PLUVIFOR (provincial pendiente)", "categoria": "simulado",
            "estado_catalogo": "simulada", "nota": NOTA_SIMULADA,
        })  # fmt: skip
    return filas


def generar() -> list[dict]:
    contorno, por_depto = _cargar_geo()
    filas = _reales()
    for f in filas:
        f["departamento"] = _departamento(por_depto, float(f["lon"]), float(f["lat"]))
    existentes = [(float(f["lat"]), float(f["lon"])) for f in filas]
    return filas + _simuladas(contorno, por_depto, existentes)


def escribir(destino: Path = SALIDA) -> None:
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(generar())


if __name__ == "__main__":
    escribir()
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
