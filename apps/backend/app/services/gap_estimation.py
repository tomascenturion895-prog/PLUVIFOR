from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol

from app.domain.enums import RainState
from app.domain.estimation import (
    MAX_KM,
    Contexto,
    Estimacion,
    EstimadorChirps,
    EstimadorVecinas,
    Vecina,
    distancia_km,
    mismo_horario,
)
from app.models import GapEstimate
from app.repositories.gap_estimates import GapEstimateRepository, Guardar, Punto


class Estimador(Protocol):
    def estimar(self, contexto: Contexto) -> Estimacion | None: ...


@dataclass
class ResultadoEstimacion:
    """Resumen de una corrida. `sin_estimar` son huecos que siguen siendo «sin dato»."""

    huecos: int = 0
    estimados: int = 0
    por_metodo: Counter[str] = field(default_factory=Counter)
    guardado: bool = False

    @property
    def sin_estimar(self) -> int:
        return self.huecos - self.estimados


class GapEstimationService:
    """Estima los días SIN DATO de una estación dentro de su propio período con datos.

    Solo toca la tabla de estimaciones: no escribe ni cambia ninguna lectura observada.
    Los métodos se prueban en orden y gana el primero que puede responder (Strategy).
    """

    def __init__(
        self,
        repository: GapEstimateRepository,
        cutoff: date,
        estimadores: Sequence[Estimador] | None = None,
        max_km: float = MAX_KM,
    ):
        self._repository = repository
        self._cutoff = cutoff
        self._estimadores = (
            list(estimadores) if estimadores else [EstimadorVecinas(max_km), EstimadorChirps()]
        )
        self._max_km = max_km

    def run(
        self,
        start: date,
        end: date,
        station_id: int | None = None,
        *,
        dry_run: bool = False,
    ) -> ResultadoEstimacion:
        end = min(end, self._cutoff)  # no se usan datos posteriores al corte
        if start > end:
            raise ValueError("«desde» no puede ser posterior a «hasta» ni al corte de datos.")
        targets = self._repository.stations(station_id)
        if station_id is not None and not targets:
            raise ValueError("No existe esa estación.")
        candidates = self._repository.neighbors_candidates()

        resultado = ResultadoEstimacion()
        guardar: list[Guardar] = []
        for target in targets:
            guardar.extend(self._estimar_estacion(target, candidates, start, end, resultado))
        if not dry_run:
            self._repository.replace([t.id for t in targets], start, end, guardar)
            resultado.guardado = True
        return resultado

    def _estimar_estacion(
        self,
        target: Punto,
        candidates: list[Punto],
        start: date,
        end: date,
        resultado: ResultadoEstimacion,
    ) -> list[Guardar]:
        span = self._repository.data_span(target.id)
        if span is None:
            return []
        first, last = max(start, span[0]), min(end, span[1])
        if first > last:
            return []
        neighbors = self._neighbors(target, candidates)
        ids = [target.id, *neighbors]
        days = self._repository.observed_days(ids, first, last)
        flagged = self._repository.flagged_days(list(neighbors), first, last)
        chirps = self._repository.chirps_values(target.id, first, last)

        salida: list[Guardar] = []
        day = first
        while day <= last:
            own = days.get((target.id, day))
            if own is None or own.state == RainState.DATO:
                day += timedelta(days=1)
                continue
            resultado.huecos += 1
            vecinas = []
            for nid, (punto, distancia) in neighbors.items():
                visto = days.get((nid, day))
                if (
                    visto is not None
                    and visto.state == RainState.DATO
                    and visto.mm is not None
                    and (nid, day) not in flagged
                ):
                    vecinas.append(Vecina(nid, punto.name, distancia, visto.mm))
            contexto = Contexto(vecinas=vecinas, chirps_mm=chirps.get(day))
            for estimador in self._estimadores:
                estimacion = estimador.estimar(contexto)
                if estimacion is not None:
                    salida.append(Guardar(target.id, day, own.state, estimacion))
                    resultado.estimados += 1
                    resultado.por_metodo[estimacion.method] += 1
                    break
            day += timedelta(days=1)
        return salida

    def _neighbors(self, target: Punto, candidates: list[Punto]) -> dict[int, tuple[Punto, float]]:
        if target.lat is None or target.lon is None:
            return {}
        cerca: dict[int, tuple[Punto, float]] = {}
        for c in candidates:
            if c.id == target.id or c.lat is None or c.lon is None:
                continue
            if not mismo_horario(target.kind, target.day_cutoff, c.kind, c.day_cutoff):
                continue
            d = distancia_km(target.lat, target.lon, c.lat, c.lon)
            if d <= self._max_km:
                cerca[c.id] = (c, d)
        return cerca

    def search(
        self, station_id: int | None, start: date | None, end: date | None, limit: int, offset: int
    ) -> tuple[list[GapEstimate], int]:
        return self._repository.search(station_id, start, end, limit, offset)
