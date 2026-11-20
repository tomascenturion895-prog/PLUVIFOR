"""Las herramientas del servidor. Todas son consultas: ninguna escribe.

Cada respuesta lleva la leyenda de prototipo y, para cada milímetro, su lectura en texto:
un día o un acumulado sin dato se dice «sin dato» y nunca se convierte en 0 mm.
"""

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from servidor_mcp import LEYENDA
from servidor_mcp.api import LectorApi

CATEGORIAS = ("observado", "referencia", "estimado")
MAX_ID = 2_147_483_647
MAX_ESTACIONES_COMPARAR = 20

NOTA = (
    "Un valor «sin dato» (mm = null) significa que no hay medición: NO es 0 mm y no quiere decir "
    "que no llovió. Observado, referencia y estimado nunca se suman ni se promedian entre sí. "
    "Fecha de corte de los datos: 31/10/2026."
)


class ArgumentoInvalido(ValueError):
    """Los argumentos de la herramienta no cumplen lo que pide. El mensaje está en español."""


# ---- Validación de argumentos (sin dependencias) ----


def _solo(args: Mapping[str, Any], permitidos: set[str]) -> None:
    extra = sorted(set(args) - permitidos)
    if extra:
        raise ArgumentoInvalido(f"Argumento desconocido: {', '.join(extra)}.")


def _entero(args: Mapping[str, Any], nombre: str, *, minimo: int, maximo: int, obligatorio: bool):
    valor = args.get(nombre)
    if valor is None:
        if obligatorio:
            raise ArgumentoInvalido(f"Falta «{nombre}».")
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ArgumentoInvalido(f"«{nombre}» tiene que ser un entero entre {minimo} y {maximo}.")
    return valor


def _fecha(args: Mapping[str, Any], nombre: str) -> str:
    valor = args.get(nombre)
    if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise ArgumentoInvalido(f"«{nombre}» tiene que ser una fecha AAAA-MM-DD.")
    try:
        date.fromisoformat(valor)
    except ValueError:
        raise ArgumentoInvalido(f"«{nombre}» no es una fecha válida.") from None
    return valor


def _texto(args: Mapping[str, Any], nombre: str, *, maximo: int = 100):
    valor = args.get(nombre)
    if valor is None:
        return None
    if not isinstance(valor, str) or not valor.strip() or len(valor) > maximo:
        raise ArgumentoInvalido(f"«{nombre}» tiene que ser un texto de hasta {maximo} caracteres.")
    return valor.strip()


def _categoria(args: Mapping[str, Any]) -> str:
    valor = args.get("categoria", "observado")
    if valor not in CATEGORIAS:
        raise ArgumentoInvalido(f"«categoria» tiene que ser una de: {', '.join(CATEGORIAS)}.")
    return valor


def _periodo(args: Mapping[str, Any]) -> tuple[str, str]:
    desde, hasta = _fecha(args, "desde"), _fecha(args, "hasta")
    if desde > hasta:
        raise ArgumentoInvalido("«desde» no puede ser posterior a «hasta».")
    return desde, hasta


# ---- Rotulado de huecos ----


def _mm_texto(mm: Any) -> str:
    return "sin dato" if mm is None else f"{mm:g} mm"


def rotular_huecos(valor: Any) -> Any:
    """Agrega la lectura en texto de cada milímetro. No cambia ni inventa ningún número.

    `mm: null` queda null y se acompaña de «sin dato»; un 0 medido sigue siendo 0 («0 mm»).
    """
    if isinstance(valor, list):
        return [rotular_huecos(item) for item in valor]
    if not isinstance(valor, dict):
        return valor
    salida = {k: rotular_huecos(v) for k, v in valor.items()}
    for campo in ("mm", "accumulated_mm"):
        if campo in valor and not isinstance(valor[campo], (dict, list)):
            salida[f"{campo}_texto"] = _mm_texto(valor[campo])
    return salida


# ---- Herramientas ----


@dataclass(frozen=True)
class Herramienta:
    nombre: str
    titulo: str
    descripcion: str
    esquema: dict[str, Any]
    ejecutar: Callable[[LectorApi, Mapping[str, Any]], Any]

    def definicion(self) -> dict[str, Any]:
        return {
            "name": self.nombre,
            "title": self.titulo,
            "description": self.descripcion,
            "inputSchema": self.esquema,
            # Todas son consultas: no cambian nada y se pueden repetir sin efecto.
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }


def _objeto(propiedades: dict[str, Any], obligatorios: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": propiedades,
        "required": obligatorios,
        "additionalProperties": False,
    }


_FECHA = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
_CATEGORIA = {"type": "string", "enum": list(CATEGORIAS), "default": "observado"}
_ESTACION = {"type": "integer", "minimum": 1, "maximum": MAX_ID}


def _listar_estaciones(lector: LectorApi, args: Mapping[str, Any]) -> Any:
    _solo(args, {"texto", "zona", "departamento", "fuente", "limite", "desde_registro"})
    return lector.get(
        "/api/stations",
        {
            "q": _texto(args, "texto"),
            "zone": _texto(args, "zona"),
            "department": _texto(args, "departamento"),
            "source": _texto(args, "fuente", maximo=64),
            "limit": _entero(args, "limite", minimo=1, maximo=200, obligatorio=False) or 50,
            "offset": _entero(args, "desde_registro", minimo=0, maximo=MAX_ID, obligatorio=False),
        },
    )


def _lluvia_por_estacion(lector: LectorApi, args: Mapping[str, Any]) -> Any:
    _solo(args, {"estacion_id", "desde", "hasta", "categoria"})
    estacion = _entero(args, "estacion_id", minimo=1, maximo=MAX_ID, obligatorio=True)
    desde, hasta = _periodo(args)
    return lector.get(
        "/api/rainfall",
        {"station_id": estacion, "from": desde, "to": hasta, "category": _categoria(args)},
    )


def _acumulado(lector: LectorApi, args: Mapping[str, Any]) -> Any:
    _solo(args, {"desde", "hasta", "estacion_id", "zona", "categoria"})
    desde, hasta = _periodo(args)
    return lector.get(
        "/api/rainfall/accumulated",
        {
            "from": desde,
            "to": hasta,
            "station_id": _entero(args, "estacion_id", minimo=1, maximo=MAX_ID, obligatorio=False),
            "zone": _texto(args, "zona"),
            "category": _categoria(args),
        },
    )


def _comparar(lector: LectorApi, args: Mapping[str, Any]) -> Any:
    _solo(args, {"estacion_ids", "desde", "hasta", "categoria"})
    ids = args.get("estacion_ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= MAX_ESTACIONES_COMPARAR:
        raise ArgumentoInvalido(
            f"«estacion_ids» tiene que ser una lista de 1 a {MAX_ESTACIONES_COMPARAR} estaciones."
        )
    validos = [
        _entero({"estacion_ids": i}, "estacion_ids", minimo=1, maximo=MAX_ID, obligatorio=True)
        for i in ids
    ]
    desde, hasta = _periodo(args)
    return lector.get(
        "/api/rainfall/compare",
        {
            "station_ids": ",".join(str(i) for i in validos),
            "from": desde,
            "to": hasta,
            "category": _categoria(args),
        },
    )


HERRAMIENTAS: tuple[Herramienta, ...] = (
    Herramienta(
        "listar_estaciones",
        "Listar estaciones",
        "Catálogo de estaciones pluviométricas de Formosa, con su fuente, red y estado de las "
        "coordenadas (pendientes si no están verificadas). Sirve para encontrar el `id` de una "
        "estación antes de pedir su lluvia.",
        _objeto(
            {
                "texto": {"type": "string", "maxLength": 100, "description": "Nombre o localidad"},
                "zona": {"type": "string", "maxLength": 100},
                "departamento": {"type": "string", "maxLength": 100},
                "fuente": {"type": "string", "maxLength": 64, "description": "Código de la fuente"},
                "limite": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                "desde_registro": {"type": "integer", "minimum": 0, "default": 0},
            },
            [],
        ),
        _listar_estaciones,
    ),
    Herramienta(
        "lluvia_por_estacion",
        "Lluvia diaria de una estación",
        "Serie diaria de una estación en un período. Cada día trae su estado (`dato`, `sin_fila` o "
        "`fila_sin_valor`), los mm (null = sin dato, nunca 0), la fuente, la categoría, las "
        "banderas de calidad y las advertencias del período (por ejemplo, una racha de ceros).",
        _objeto(
            {
                "estacion_id": _ESTACION,
                "desde": {**_FECHA, "description": "AAAA-MM-DD"},
                "hasta": {**_FECHA, "description": "AAAA-MM-DD; no pasa del corte 2026-10-31"},
                "categoria": _CATEGORIA,
            },
            ["estacion_id", "desde", "hasta"],
        ),
        _lluvia_por_estacion,
    ),
    Herramienta(
        "acumulado",
        "Acumulado de lluvia",
        "Acumulado de un período, uno por estación (no se suman entre estaciones): de toda la red, "
        "de una estación o de una zona. Si no hay ningún día con dato, el acumulado es «sin dato», "
        "no 0 mm. Incluye cobertura y los días sin dato aparte. Esta respuesta NO trae "
        "advertencias de calidad: un 0 mm en un período largo puede ser un sensor trabado; para "
        "verlo usá `lluvia_por_estacion` o `comparar_estaciones`.",
        _objeto(
            {
                "desde": _FECHA,
                "hasta": _FECHA,
                "estacion_id": _ESTACION,
                "zona": {"type": "string", "maxLength": 100},
                "categoria": _CATEGORIA,
            },
            ["desde", "hasta"],
        ),
        _acumulado,
    ),
    Herramienta(
        "comparar_estaciones",
        "Comparar estaciones y ver advertencias",
        "Compara las series de varias estaciones en un período y devuelve las advertencias de "
        "comparabilidad: horario de corte distinto, observado vs. estimado, cobertura despareja, "
        "dato sin validar, racha de ceros de 60 días o más e inconsistencia con estaciones "
        "vecinas. Leelas antes de sacar conclusiones de la comparación.",
        _objeto(
            {
                "estacion_ids": {
                    "type": "array",
                    "items": _ESTACION,
                    "minItems": 1,
                    "maxItems": MAX_ESTACIONES_COMPARAR,
                },
                "desde": _FECHA,
                "hasta": _FECHA,
                "categoria": _CATEGORIA,
            },
            ["estacion_ids", "desde", "hasta"],
        ),
        _comparar,
    ),
)

POR_NOMBRE = {h.nombre: h for h in HERRAMIENTAS}


def llamar(nombre: str, args: Mapping[str, Any], lector: LectorApi) -> str:
    """Ejecuta una herramienta y arma el texto. Puede lanzar ArgumentoInvalido o ErrorConsulta."""
    herramienta = POR_NOMBRE[nombre]
    resultado = herramienta.ejecutar(lector, args)
    return json.dumps(
        {"leyenda": LEYENDA, "nota": NOTA, "resultado": rotular_huecos(resultado)},
        ensure_ascii=False,
        indent=2,
    )
