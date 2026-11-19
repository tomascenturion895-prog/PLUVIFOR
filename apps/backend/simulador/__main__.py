"""Uso: python -m simulador --url http://localhost:8000 --dispositivos 3 --dias 7

La clave sale de DEVICE_API_KEY (variable de entorno o .env), nunca de la línea de comandos.
"""

import argparse
import sys
from datetime import date

from app.config import get_settings
from simulador.cliente import enviar_lecturas, validar_url
from simulador.generador import generar_lecturas


def main(argv: list[str] | None = None) -> int:
    ajustes = get_settings()
    parser = argparse.ArgumentParser(prog="simulador", description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000", help="dirección de la API")
    parser.add_argument("--dispositivos", type=int, default=3)
    parser.add_argument("--dias", type=int, default=7)
    parser.add_argument(
        "--hasta",
        type=date.fromisoformat,
        default=ajustes.data_cutoff_date,
        help="último día a simular (por defecto, el corte de datos)",
    )
    parser.add_argument("--semilla", type=int, default=1)
    args = parser.parse_args(argv)

    clave = ajustes.device_api_key.get_secret_value() if ajustes.device_api_key else ""
    if not clave:
        print("Falta DEVICE_API_KEY (en el entorno o en el .env).", file=sys.stderr)
        return 2
    if args.hasta > ajustes.data_cutoff_date:
        print(f"«--hasta» no puede pasar del corte ({ajustes.data_cutoff_date}).", file=sys.stderr)
        return 2
    try:
        url = validar_url(args.url)
        lecturas = generar_lecturas(
            dispositivos=args.dispositivos, dias=args.dias, hasta=args.hasta, semilla=args.semilla
        )
        resultado = enviar_lecturas(lecturas, url, clave)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    print(
        f"Lecturas SIMULADAS enviadas: {resultado.creadas} nuevas, "
        f"{resultado.repetidas} repetidas, {resultado.rechazadas} rechazadas."
    )
    for error in resultado.errores:
        print(f"  - {error}", file=sys.stderr)
    return 1 if resultado.detenido or resultado.rechazadas else 0


if __name__ == "__main__":
    sys.exit(main())
