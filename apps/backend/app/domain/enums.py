"""Vocabulario cerrado del dominio. Los valores son los que se guardan y se devuelven."""

from enum import StrEnum


class RainState(StrEnum):
    """Estado de un día de una estación. Solo `DATO` lleva milímetros."""

    DATO = "dato"
    FILA_SIN_VALOR = "fila_sin_valor"
    SIN_FILA = "sin_fila"


class DataCategory(StrEnum):
    """Observado, referencia y estimado nunca se suman ni se promedian entre sí."""

    OBSERVADO = "observado"
    REFERENCIA = "referencia"
    ESTIMADO = "estimado"


class Validation(StrEnum):
    VALIDADO = "validado"
    SIN_VALIDAR = "sin_validar"


class CoordsStatus(StrEnum):
    VERIFICADA = "verificada"
    PENDIENTE = "pendiente"


class Severity(StrEnum):
    """Descriptiva: no es una alerta de riesgo."""

    AVISO = "aviso"
    ALERTA = "alerta"


class ImportMode(StrEnum):
    AUDIT = "audit"
    COMMIT = "commit"


class ImportStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class ReportLocation(StrEnum):
    """La ubicación de un reporte de campo: si no se informó, queda pendiente, no se inventa."""

    INFORMADA = "informada"
    PENDIENTE = "pendiente"


class LocationSource(StrEnum):
    """Cómo se obtuvo la ubicación de un reporte de campo."""

    DISPOSITIVO = "dispositivo"
    MANUAL = "manual"


class SensorCategory(StrEnum):
    """Categoría de una lectura de sensor. Hoy no hay hardware real: todo entra como `simulado`.

    Una lectura simulada nunca se suma ni se promedia con lo observado, lo de referencia ni
    lo estimado. Aceptar sensores reales sería una decisión y una categoría nueva.
    """

    SIMULADO = "simulado"
