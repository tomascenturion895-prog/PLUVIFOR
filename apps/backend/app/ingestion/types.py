"""Tipos que circulan entre las etapas de la importación (sin dependencias externas)."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from app.domain.enums import DataCategory, RainState, Validation


class RejectionReason(StrEnum):
    """Nada se descarta en silencio: cada rechazo lleva uno de estos motivos."""

    FECHA_INVALIDA = "fecha_invalida"
    FECHA_POSTERIOR_AL_CORTE = "fecha_posterior_al_corte"
    ESTACION_INEXISTENTE = "estacion_inexistente"
    MM_INVALIDO = "mm_invalido"
    MM_NEGATIVO = "mm_negativo"
    ESTADO_INVALIDO = "estado_invalido"
    ESTADO_INCOHERENTE = "estado_incoherente"
    CATEGORIA_INVALIDA = "categoria_invalida"
    UNIDAD_INVALIDA = "unidad_invalida"
    DUPLICADO_EN_ARCHIVO = "duplicado_en_archivo"
    COORDENADAS_INVALIDAS = "coordenadas_invalidas"
    CODIGO_VACIO = "codigo_vacio"


@dataclass(frozen=True)
class RawRainRow:
    """Fila tal como viene del archivo: todo texto, sin interpretar."""

    line: int
    station_code: str
    obs_date: str
    mm: str
    mm_chrono: str
    unit: str
    state: str
    category: str


@dataclass(frozen=True)
class RainRow:
    """Fila válida. `mm` es None salvo que el estado sea `dato`."""

    station_code: str
    obs_date: date
    state: RainState
    mm: float | None
    mm_chrono: float | None
    category: DataCategory
    validation: Validation = Validation.SIN_VALIDAR


@dataclass(frozen=True)
class Rejection:
    line: int
    reason: RejectionReason


@dataclass(frozen=True)
class StationRow:
    """Estación del catálogo. Las coordenadas vacías quedan vacías (pendientes)."""

    code: str
    internal_code: str | None
    name: str
    kind: str | None
    locality: str | None
    lat: float | None
    lon: float | None
    elevation_m: float | None
    active_from: date | None
    active_to: date | None


@dataclass
class ImportReport:
    filename: str
    sha256: str
    mode: str
    rows_read: int = 0
    accepted: list[RainRow | StationRow] = field(default_factory=list)
    rejections: list[Rejection] = field(default_factory=list)
    inserted: int = 0
    updated: int = 0

    @property
    def rows_accepted(self) -> int:
        return len(self.accepted)

    @property
    def rows_rejected(self) -> int:
        return len(self.rejections)

    def rejections_by_reason(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rejection in self.rejections:
            counts[rejection.reason.value] = counts.get(rejection.reason.value, 0) + 1
        return counts
