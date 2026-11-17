"""Descarga las series diarias del SIGA (INTA) de las tres estaciones de Formosa.

Guarda cada respuesta del servidor tal como llega, sin modificarla, en ./original/.
El servidor devuelve como maximo 1000 filas por pedido; por eso se pide de a dos anios.

Uso:  python descargar_siga.py
Requiere Python 3.8 o superior. No necesita paquetes externos.
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://siga.inta.gob.ar/LiGVV1gb54QrVSDc.php"
CORTE = "31-10-2026"  # fecha de corte del kit: no se pide nada posterior
# id del SIGA: (primer anio con datos, ultimo anio con datos)
ESTACIONES = {51: (1960, 2015), 424: (2013, 2022), 425: (2013, 2023)}
SALIDA = Path(__file__).parent / "original"


def pedir(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "spaidycode-reporte-pluvial (uso educativo)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    consultado = datetime.now(timezone.utc).isoformat()
    catalogo = pedir(f"{BASE}?param_type=estacion&param_value=")
    (SALIDA / "siga_estaciones_catalogo.json").write_text(catalogo, encoding="utf-8")
    indice = []
    for est, (desde, hasta) in ESTACIONES.items():
        total = 0
        for anio in range(desde, hasta + 1, 2):
            a = f"01-01-{anio}"
            b = CORTE if anio + 1 >= 2026 else f"31-12-{anio + 1}"
            url = f"{BASE}?param_type=diario&param_value={est}/{a}/{b}"
            texto = pedir(url)
            filas = len(json.loads(texto)) if texto.strip() else 0  # respuesta vacia = sin filas en ese rango
            if filas >= 1000:
                raise SystemExit(f"Respuesta truncada en {url}: achicar la ventana")
            nombre = f"siga_diario_{est}_{anio}_{anio + 1}.json"
            (SALIDA / nombre).write_text(texto, encoding="utf-8")
            indice.append({"archivo": nombre, "url": url, "filas": filas, "consultado": consultado})
            total += filas
            time.sleep(0.3)  # no saturar el servidor
        print(f"estacion {est}: {total} filas")
    (SALIDA / "indice_descarga.json").write_text(json.dumps(indice, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
