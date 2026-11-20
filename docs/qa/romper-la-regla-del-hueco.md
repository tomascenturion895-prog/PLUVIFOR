# Comprobación: romper la regla del hueco hace fallar las pruebas

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-55. El criterio dice que «romper la regla del hueco hace fallar una prueba». Se comprobó rompiendo el código a propósito, una vez por vez, y corriendo `pytest`. Después de cada prueba se restauró el código original.

| # | Rotura que se introdujo | Dónde | Resultado |
|---|---|---|---|
| M1 | Un período sin ningún dato da 0 en lugar de «sin dato» | `app/domain/metrics.py`, `summarize` | **Fallan 5 pruebas**, entre ellas `test_period_without_any_data_has_null_accumulated_not_zero` y `test_caso3_la_racha_termina_donde_hay_un_hueco_no_un_cero` |
| M2 | El acumulado SQL devuelve 0 cuando no hay ningún dato | `app/repositories/series.py`, acumulado por zona | **Fallan 6 pruebas**, entre ellas `test_zona_sin_ningun_dato_da_null_no_cero` y `test_only_gaps_gives_null_not_zero` |
| M3 | Un valor vacío del archivo se importa como 0,0 en lugar de hueco | `app/ingestion/validation.py`, `_number` | **Fallan al menos 8 pruebas** (de importación, de la API y de la demo), entre ellas `test_the_gap_is_stored_without_millimeters_never_zero` |
| M4 | El umbral de la racha de ceros pasa de 60 a 61 días | `app/domain/quality.py`, `ZERO_STREAK_MIN_DAYS` | **Fallan 4 pruebas**, entre ellas `test_streak_of_exactly_60_is_flagged` |
| M5 | El comparador devuelve 0 en los días sin dato (`mm=d.mm or 0.0`) | `app/api/rainfall.py`, `compare_rainfall` | **Falla** `test_compare_two_stations_returns_aligned_series_and_warnings` (19/11) |
| M6 | La serie de una estación devuelve 0 en los días sin dato (`"mm": d.mm or 0.0`) | `app/api/rainfall.py`, `get_rainfall` | **Falla** `test_series_keeps_gaps_as_null_never_zero` (19/11) |
| M7 | En Go, un día `sin_fila` sale con 0 mm | `apps/api-go/internal/rainfall`, `FillCalendar` | **Falla** `TestParidadConPython` (19/11) |
| M8 | En Go, el umbral de cobertura baja pasa de 0,8 a 0,5, o las banderas de cada día se corren un día | `apps/api-go/internal/rainfall` | **Falla** `TestParidadConPython` en las dos (19/11) |

Las listas de fallas se cortaron a las primeras que muestra `pytest`, así que puede haber más. En las cuatro roturas falló al menos una prueba.

## Cómo repetirlo

```
cd apps/backend
# 1. editar a mano una de las líneas de la tabla (por ejemplo, M1)
pytest -q          # tiene que fallar
git checkout -- app   # restaurar
```

## Qué no cubre

- Son cuatro roturas elegidas a mano, no una herramienta de mutaciones automática. No prueba que no existan otras roturas que pasen sin que falle nada.
- M5 a M8 se agregaron el 19/11 al entregarse el comparador y las rutas de Go. Siguen sin cubrir el informe (`/api/reports/summary`) ni la salud de la red.
- El CI ya corre `pytest` en cada PR (`.github/workflows/ci.yml`); no se modificó.
