"""Descarga las series diarias del SIGA (INTA) de las tres estaciones de Formosa.

Guarda cada respuesta del servidor tal como llega, sin modificarla, en ./original/.
El servidor devuelve como maximo 1000 filas por pedido; por eso se pide de a dos anios.
Una respuesta vacia se guarda vacia: significa que el SIGA no tiene filas en ese rango.

El SIGA cambia el nombre de su archivo de datos de tanto en tanto (el original ya dejo de
existir). Por eso el script lo busca en el codigo del sitio y prueba cada candidato.

Uso:  python descargar_siga.py
Requiere Python 3.8 o superior. No necesita paquetes externos.
Variable opcional: SIGA_URL (por defecto https://siga.inta.gob.ar), pensada para pruebas.
"""
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOST = os.environ.get("SIGA_URL", "https://siga.inta.gob.ar").rstrip("/")
CORTE = "31-10-2026"  # fecha de corte del kit: no se pide nada posterior
# id del SIGA: (primer anio con datos, ultimo anio con datos)
ESTACIONES = {51: (1960, 2015), 424: (2013, 2022), 425: (2013, 2023)}
SALIDA = Path(__file__).parent / "original"


def pedir(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "spaidycode-reporte-pluvial (uso educativo)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def encontrar_endpoint() -> str:
    """Busca en el JavaScript del sitio los archivos .php y se queda con el que devuelve el catalogo."""
    candidatos = []
    for js in ("/js/urlserver.js", "/js/main.js"):
        try:
            candidatos += re.findall(r"[A-Za-z0-9]{12,}\.php", pedir(HOST + js))
        except OSError:
            continue
    for php in dict.fromkeys(candidatos):  # sin repetidos, en orden
        try:
            datos = json.loads(pedir(f"{HOST}/{php}?param_type=estacion&param_value="))
        except (OSError, ValueError):
            continue
        if isinstance(datos, list) and datos:
            return f"{HOST}/{php}"
    raise SystemExit("No se encontro el endpoint de datos del SIGA: el sitio cambio. Revisar a mano.")


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    base = encontrar_endpoint()
    consultado = datetime.now(timezone.utc).isoformat()
    (SALIDA / "siga_estaciones_catalogo.json").write_text(
        pedir(f"{base}?param_type=estacion&param_value="), encoding="utf-8", newline=""
    )
    indice = []
    for est, (desde, hasta) in ESTACIONES.items():
        total = 0
        for anio in range(desde, hasta + 1, 2):
            a = f"01-01-{anio}"
            b = CORTE if anio + 1 >= 2026 else f"31-12-{anio + 1}"
            texto = pedir(f"{base}?param_type=diario&param_value={est}/{a}/{b}")
            filas = len(json.loads(texto)) if texto.strip() else 0  # respuesta vacia = sin filas en ese rango
            if filas >= 1000:
                raise SystemExit(f"Respuesta truncada en estacion {est}, {a} a {b}: achicar la ventana")
            nombre = f"siga_diario_{est}_{anio}_{anio + 1}.json"
            (SALIDA / nombre).write_text(texto, encoding="utf-8", newline="")
            indice.append({"archivo": nombre, "estacion": est, "desde": a, "hasta": b, "filas": filas, "consultado": consultado})
            total += filas
            time.sleep(0.3)  # no saturar el servidor
        print(f"estacion {est}: {total} filas")
    (SALIDA / "indice_descarga.json").write_text(
        json.dumps(indice, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
