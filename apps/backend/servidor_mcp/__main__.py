"""Uso: python -m servidor_mcp [--api-url http://localhost:8080]

Habla MCP por la entrada y salida estándar. Los mensajes de diagnóstico van a stderr: stdout
es solo para el protocolo. Cómo conectarlo: docs/entrega/mcp.md.
"""

import argparse
import os
import sys

from servidor_mcp.api import LectorHttp
from servidor_mcp.servidor import ServidorMcp, servir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="servidor_mcp", description=__doc__)
    parser.add_argument(
        "--api-url",
        default=os.environ.get("PLUVIFOR_API_URL", "http://localhost:8080"),
        help="dirección de la API (por defecto PLUVIFOR_API_URL o la API en Go)",
    )
    args = parser.parse_args(argv)
    try:
        lector = LectorHttp(args.api_url)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    print(f"PLUVIFOR MCP (solo lectura) conectado a {args.api_url}", file=sys.stderr)
    servir(sys.stdin, sys.stdout, ServidorMcp(lector))
    return 0


if __name__ == "__main__":
    sys.exit(main())
