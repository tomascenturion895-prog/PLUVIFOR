"""Cliente del SIGA en vivo (SCRUM-64). Es un extra: si falla, se usa el CSV versionado.

El endpoint no se inventa: se descubre igual que en `docs/datos/descargar_siga.py`, buscando en el
JavaScript del sitio los archivos .php y quedándose con el que devuelve el catálogo de estaciones.
La red va en una función inyectada (`fetch`), así las pruebas no necesitan internet.

Esto **no está verificado contra el SIGA real**: se escribió y probó con respuestas simuladas, con
el formato de las respuestas originales guardadas en `docs/datos/original/`.
"""

import csv
import io
import json
import re
import urllib.request
from collections.abc import Callable
from datetime import date, timedelta

Fetch = Callable[[str], str]

DEFAULT_HOST = "https://siga.inta.gob.ar"
# El servidor devuelve como máximo 1.000 filas por pedido: se pide de a 730 días.
WINDOW_DAYS = 730
MAX_ROWS = 1000
COLUMNS = [
    "estacion_id", "estacion", "fecha", "mm_pluviometrica", "mm_cronologica",
    "unidad", "estado", "bandera", "categoria", "fuente",
]  # fmt: skip


class SigaUnavailableError(Exception):
    """El SIGA no respondió o cambió su formato. Quien llama decide si usa el respaldo."""


def http_fetch(url: str) -> str:
    if not url.startswith("https://"):
        raise SigaUnavailableError("Solo se consulta el SIGA por https.")
    request = urllib.request.Request(  # noqa: S310 (solo https, verificado arriba)
        url, headers={"User-Agent": "spaidycode-reporte-pluvial (uso educativo)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return response.read().decode("utf-8")
    except (OSError, ValueError) as exc:
        raise SigaUnavailableError(f"No se pudo consultar el SIGA: {exc}") from exc


def _day(value: date) -> str:
    return value.strftime("%d-%m-%Y")


class SigaLiveClient:
    def __init__(self, fetch: Fetch = http_fetch, host: str = DEFAULT_HOST):
        self._fetch = fetch
        self._host = host.rstrip("/")
        self._endpoint: str | None = None

    def discover_endpoint(self) -> str:
        if self._endpoint:
            return self._endpoint
        candidates: list[str] = []
        errors: list[str] = []
        for script in ("/js/urlserver.js", "/js/main.js"):
            try:
                candidates += re.findall(r"[A-Za-z0-9]{12,}\.php", self._fetch(self._host + script))
            except SigaUnavailableError as exc:
                errors.append(str(exc))
        if not candidates and errors:  # sin red no es lo mismo que «el sitio cambió»
            raise SigaUnavailableError(errors[-1])
        for php in dict.fromkeys(candidates):
            try:
                data = json.loads(
                    self._fetch(f"{self._host}/{php}?param_type=estacion&param_value=")
                )
            except (SigaUnavailableError, ValueError):
                continue
            if isinstance(data, list) and data:
                self._endpoint = f"{self._host}/{php}"
                return self._endpoint
        raise SigaUnavailableError("No se encontró el endpoint de datos del SIGA: el sitio cambió.")

    def daily(self, station: int, start: date, end: date) -> list[dict]:
        base = self.discover_endpoint()
        rows: list[dict] = []
        cursor = start
        while cursor <= end:
            window_end = min(cursor + timedelta(days=WINDOW_DAYS - 1), end)
            url = (
                f"{base}?param_type=diario&param_value={station}/{_day(cursor)}/{_day(window_end)}"
            )
            text = self._fetch(url)
            try:
                chunk = json.loads(text) if text.strip() else []  # vacío = sin filas en el rango
            except ValueError as exc:
                raise SigaUnavailableError("El SIGA devolvió una respuesta ilegible.") from exc
            if not isinstance(chunk, list):
                raise SigaUnavailableError("El SIGA devolvió un formato inesperado.")
            if len(chunk) >= MAX_ROWS:
                raise SigaUnavailableError("Respuesta truncada del SIGA: la ventana es muy grande.")
            rows += chunk
            cursor = window_end + timedelta(days=1)
        return rows


def _mm(value: object) -> str:
    return "" if value is None else repr(float(value)).removesuffix(".0")


def rows_to_csv(station: int, rows: list[dict], start: date, end: date) -> str:
    """Pasa las filas del SIGA al CSV que ya entiende el importador, día por día.

    Un día con valor es `dato` (un 0 es un dato); un día que el SIGA devuelve sin valor es
    `fila_sin_valor`; un día que el SIGA no devuelve es `sin_fila`. Ninguno de los dos huecos es 0.
    """
    by_day: dict[date, dict] = {}
    for row in rows:
        by_day[date.fromisoformat(str(row["fechaHora"])[:10])] = row
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    day = start
    while day <= end:
        row = by_day.get(day)
        if row is None:
            values = ("", "", "sin_fila")
        elif row.get("precDiaPlub") is None:
            values = ("", _mm(row.get("precDiaCrono")), "fila_sin_valor")
        else:
            values = (_mm(row["precDiaPlub"]), _mm(row.get("precDiaCrono")), "dato")
        writer.writerow(
            [station, "", day.isoformat(), values[0], values[1], "mm", values[2], "", "OBSERVADO",
             "SIGA INTA (en vivo)"]
        )  # fmt: skip
        day += timedelta(days=1)
    return out.getvalue()
