"""Reglas de aceptación de una fila. Puras: reciben datos, devuelven fila válida o motivo."""

import math
from datetime import date

from app.domain.enums import DataCategory, RainState
from app.ingestion.types import RainRow, RawRainRow, RejectionReason


class RowValidator:
    def __init__(self, cutoff: date, known_stations: set[str]):
        self._cutoff = cutoff
        self._known_stations = known_stations
        self._seen: set[tuple[str, date, DataCategory]] = set()

    def validate(self, raw: RawRainRow) -> RainRow | RejectionReason:
        if raw.station_code not in self._known_stations:
            return RejectionReason.ESTACION_INEXISTENTE
        try:
            obs_date = date.fromisoformat(raw.obs_date)
        except ValueError:
            return RejectionReason.FECHA_INVALIDA
        if obs_date > self._cutoff:
            return RejectionReason.FECHA_POSTERIOR_AL_CORTE
        if raw.unit != "mm":
            return RejectionReason.UNIDAD_INVALIDA
        try:
            category = DataCategory(raw.category.lower())
        except ValueError:
            return RejectionReason.CATEGORIA_INVALIDA
        try:
            state = RainState(raw.state)
        except ValueError:
            return RejectionReason.ESTADO_INVALIDO

        mm = self._number(raw.mm)
        mm_chrono = self._number(raw.mm_chrono)
        for value in (mm, mm_chrono):
            if value is RejectionReason.MM_INVALIDO:
                return RejectionReason.MM_INVALIDO
            if isinstance(value, float) and value < 0:
                return RejectionReason.MM_NEGATIVO

        # Un hueco nunca es 0 mm: hay valor si y solo si el estado es «dato».
        if (state is RainState.DATO) != isinstance(mm, float):
            return RejectionReason.ESTADO_INCOHERENTE

        key = (raw.station_code, obs_date, category)
        if key in self._seen:
            return RejectionReason.DUPLICADO_EN_ARCHIVO
        self._seen.add(key)
        return RainRow(
            station_code=raw.station_code,
            obs_date=obs_date,
            state=state,
            mm=mm if isinstance(mm, float) else None,
            mm_chrono=mm_chrono if isinstance(mm_chrono, float) else None,
            category=category,
        )

    @staticmethod
    def _number(text: str) -> float | None | RejectionReason:
        """Vacío → None (hueco); número → float; cualquier otra cosa → inválido."""
        if text == "":
            return None
        try:
            value = float(text)
        except ValueError:
            return RejectionReason.MM_INVALIDO
        return value if math.isfinite(value) else RejectionReason.MM_INVALIDO
