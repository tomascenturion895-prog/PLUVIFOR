from datetime import date

from pydantic import BaseModel

from app.domain.enums import DataCategory

AVISO_RECURRENCIA = (
    "Frecuencia histórica de días de lluvia intensa en el período observado. No es una "
    "predicción ni una alerta: que haya ocurrido cada tantos años no dice cuándo volverá a ocurrir."
)


class YearCountOut(BaseModel):
    year: int
    valid_days: int
    ge50: int
    ge100: int


class RecurrenceOut(BaseModel):
    station_id: int
    station_name: str
    category: DataCategory
    date_from: date
    date_to: date
    clipped_to_cutoff: bool
    # Días con dato válido y sus equivalentes en años: es la base de la frecuencia.
    valid_days: int
    observed_years: float
    # Días con dato dentro de una racha de ceros prolongados: no se cuentan (pueden ser falsos).
    excluded_zero_run_days: int
    # Días sin dato (sin_fila o fila_sin_valor): no se cuentan como lluvia ni como seco.
    gap_days: int
    # False si hay menos de 5 años de dato válido: entonces no se informa ninguna frecuencia.
    sufficient_history: bool
    min_observed_years: float
    ge50: int
    ge100: int
    ge50_per_year: float | None
    ge100_per_year: float | None
    ge50_every_years: float | None
    ge100_every_years: float | None
    by_year: list[YearCountOut]
    notice: str = AVISO_RECURRENCIA
