# Plan de pruebas y criterios de aceptación

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-41. **Estado: borrador para que el equipo lo revise. Todavía no está aprobado** (el «hecho cuando» de la tarea pide esa aprobación; queda en la sección final).

Cada criterio se responde con **sí o no**. «Auto» quiere decir que ya lo cubre una prueba automática (se nombra el archivo en `apps/backend/tests/` o `apps/frontend/src/`); «Manual» quiere decir que lo mira una persona. Un criterio sin prueba automática figura como **Manual** o **Falta prueba**.

## Reglas que valen para todos los módulos

- **Un hueco no es 0 mm.** En cada módulo hay al menos un criterio que lo verifica (marcados con ★).
- Observado, referencia y estimado nunca se suman ni se promedian entre sí.
- Los datos llegan hasta el 31/10/2026; nada posterior.
- Todo dato muestra su fuente y su categoría.
- Los textos de la interfaz y de los errores están en español.

## Datos de prueba

- **Demo:** `python -m app.cli reset-demo --yes` carga el SIGA/INTA real (estaciones 51, 424 y 425). Caso de referencia: la 424 marca 0 mm durante 281 días seguidos (2015-09-20 a 2016-06-26) mientras la 425 registra 1.265 mm.
- **Entradas inválidas que se prueban en todos los módulos que las reciben:** fecha mal escrita, fecha invertida, estación inexistente, identificador negativo o cero, rango de más de 3.660 días, archivo corrupto, archivo que no es CSV, archivo vacío.

## 1. Ingesta (conectores y normalización)

| # | Criterio | Cómo |
|---|---|---|
| 1.1 | ★ Un día que la fuente no devuelve queda guardado como `sin_fila`, no como 0 mm. | Auto: `test_connectors.py`, `test_import_real_data.py` |
| 1.2 | ★ Un día que la fuente devuelve con el valor vacío queda como `fila_sin_valor`, no como 0 mm. | Auto: `test_connectors.py` |
| 1.3 | Un 0 que la fuente informa queda como `dato` con valor 0 (un cero real no se pierde). | Auto: `test_connectors.py` |
| 1.4 | Cargar dos veces el mismo archivo no duplica filas. | Auto: `test_import.py` |
| 1.5 | Con los datos reales del SIGA se leen 7.648 filas, ninguna rechazada, con 5.265 `dato`, 365 `fila_sin_valor` y 2.018 `sin_fila` (los números de `docs/datos/LEEME_siga.md`). | Auto: `test_import_real_data.py` |

## 2. Calidad del dato (banderas y advertencias)

| # | Criterio | Cómo |
|---|---|---|
| 2.1 | ★ Una racha de 60 días o más con 0 mm se marca `ceros_prolongados`; una de 59 no. | Auto: `test_quality.py` |
| 2.2 | ★ La demo deja una racha de ceros marcada (la de la estación 424). Que dure exactamente 281 días (2015-09-20 a 2016-06-26) **no tiene prueba automática**: se mira a mano en la ficha de la 424. | Auto parcial: `test_demo_reset.py`; largo: Manual |
| 2.3 | Un hueco corta una racha de ceros: no se cuenta como cero. | Auto: `test_quality.py` |
| 2.4 | Cada una de las seis advertencias (horario de corte distinto, observado vs. estimado, cobertura despareja, dato sin validar, racha de ceros, inconsistencia con vecinas) se dispara por separado. | Auto: `test_warnings.py`, `test_rainfall_api.py` (**verificar que estén las seis**) |
| 2.5 | Dos series con el mismo horario de corte no muestran la advertencia de horario distinto. | Auto: `test_warnings.py` |

## 3. API (lectura)

| # | Criterio | Cómo |
|---|---|---|
| 3.1 | ★ `GET /api/rainfall` devuelve los días sin dato como `null` con su estado, nunca como 0. | Auto: `test_rainfall_api.py` |
| 3.2 | ★ El acumulado de un período sin ningún dato es «sin dato» (`null`), no 0 mm. | Auto: `test_accumulated_api.py` |
| 3.3 | El acumulado informa cuántos días tienen dato y cuántos no. | Auto: `test_accumulated_api.py` |
| 3.4 | Estación inexistente: responde 404 con mensaje en español. | Auto: `test_stations_api.py`, `test_rainfall_api.py` |
| 3.5 | Fecha mal escrita, `from` posterior a `to` o `station_id` menor que 1: responde 422. | Auto: `test_rainfall_api.py` |
| 3.6 | Rango de más de 3.660 días: responde 422 `range_too_large`. | Auto: `test_rainfall_api.py` |
| 3.7 | Pedir estación y zona a la vez, o zona sin estaciones, da error claro. | Auto: `test_accumulated_api.py` |
| 3.8 | Cada respuesta con datos trae su fuente y su categoría. | Auto: `test_stations_api.py`, `test_rainfall_api.py` |
| 3.9 | `GET /health` responde ok. | Auto: `test_health.py` |
| 3.10 | `GET /api/rainfall/compare` (comparar estaciones): **falta**; es la tarea SCRUM-36, en curso. Sus criterios se agregan cuando se entregue. | Falta prueba |

## 4. Mapa provincial

La pantalla todavía no está implementada (SCRUM-50). Criterios previstos:

| # | Criterio | Cómo |
|---|---|---|
| 4.1 | ★ Una estación sin dato en el período se ve distinta de una con 0 mm. | Manual |
| 4.2 | Las estaciones sin coordenadas verificadas no se dibujan en un lugar inventado. | Manual |
| 4.3 | Cada punto muestra el nombre, la fuente y la categoría de la estación. | Manual |
| 4.4 | La leyenda del prototipo está visible. | Manual |

## 5. Comparador

La pantalla todavía no está implementada (SCRUM-51). Criterios previstos:

| # | Criterio | Cómo |
|---|---|---|
| 5.1 | ★ Un día sin dato en una de las estaciones no se cuenta como 0 en la comparación. | Manual |
| 5.2 | Al comparar redes con horario de corte distinto aparece esa advertencia. | Manual |
| 5.3 | Observado, referencia y estimado se muestran en series separadas. | Manual |
| 5.4 | Elegir menos de dos estaciones muestra un mensaje claro, no una pantalla vacía. | Manual |

## 6. Parte pluvial

| # | Criterio | Cómo |
|---|---|---|
| 6.1 | ★ El parte de un período sin datos dice «sin dato», no 0 mm. | Auto: `test_report.py`, `Parte.test.tsx` |
| 6.2 | Dos estaciones con corte horario distinto muestran la advertencia en el parte. | Auto: `test_report.py` |
| 6.3 | Los eventos intensos (50 mm y 100 mm) y la racha seca se informan de forma descriptiva, sin interpretar. | Auto: `test_report.py` |
| 6.4 | Pedir 0 estaciones o más del máximo permitido responde 422. | Auto: `test_report.py` |
| 6.5 | El parte se imprime sin los botones ni el menú. | Manual |
| 6.6 | El parte lleva la fecha de corte y la leyenda del prototipo. | Manual |

## 7. Importación (auditoría y confirmación)

| # | Criterio | Cómo |
|---|---|---|
| 7.1 | La auditoría no guarda nada hasta que se confirma (ni datos ni registro). | Auto: `test_import_api.py` |
| 7.2 | ★ Un día sin valor en el archivo se informa como hueco, no como 0 mm. | Auto: `test_import.py` |
| 7.3 | Faltan columnas, archivo vacío o que no es CSV: responde 422 `invalid_file` con el motivo en español. | Auto: `test_import.py`, `test_upload_security.py` |
| 7.4 | Un archivo mayor al límite (5 MB) responde 413. | Auto: `test_upload_security.py` |
| 7.5 | Confirmar sin la clave de administración responde 401. | Auto: `test_admin_key.py` |
| 7.6 | Al confirmar queda un registro de qué se cargó y qué se descartó, visible en `GET /api/import/logs`. | Auto: `test_import_api.py` |
| 7.7 | Tras confirmar lluvia se recalculan las banderas de calidad. | Auto: `test_import_api.py` |
| 7.8 | En la pantalla, «Confirmar» está bloqueado si no se auditó o si la auditoría no aceptó ninguna fila. | Auto: `Importar.test.tsx` |

## 8. Seguridad básica

| # | Criterio | Cómo |
|---|---|---|
| 8.1 | Las respuestas llevan los encabezados de seguridad. | Auto: `test_security.py` |
| 8.2 | Un cuerpo mayor a 64 KB en los pedidos que no son de carga responde 413. | Auto: `test_security.py` |
| 8.3 | Pasado el límite de pedidos por minuto responde 429. | Auto: `test_security.py` |
| 8.4 | Ningún mensaje de error deja ver rutas internas ni el texto de una excepción. | Auto: `test_errors.py` |

## 9. Pantallas (frontend)

| # | Criterio | Cómo |
|---|---|---|
| 9.1 | ★ La ficha de estación muestra «sin dato» para los días sin dato y 0 mm solo cuando el dato es 0. | Auto: `Estacion.test.tsx`, `SerieDiaria.test.ts` |
| 9.2 | Las insignias de categoría y las seis advertencias tienen texto, no solo color. | Auto: `Insignias.test.tsx` |
| 9.3 | Cargando, error y sin resultados se ven distintos entre sí. | Auto: `Estados.test.tsx` |
| 9.4 | Se puede recorrer cada pantalla solo con el teclado. | Manual |
| 9.5 | Se ve bien en un teléfono (SCRUM-71). | Manual, en equipos reales |

## Cómo se corre

```
cd apps/backend  && pytest && ruff check . && ruff format --check .
cd apps/frontend && npm test && npm run lint && npm run format:check && npm run build
```

## Qué falta

- **Aprobación del equipo.** Este plan es un borrador. Cada integrante debería revisar los módulos que le tocan y responder si los criterios son claros y verificables.
- Criterios de la comparación de estaciones (SCRUM-36), el mapa (SCRUM-50) y el comparador (SCRUM-51), cuando esas tareas se entreguen.
- Verificar que las pruebas nombradas cubren de verdad cada criterio. Las referencias a archivos de prueba son por tema; no se revisó prueba por prueba. Si alguna no lo cubre, el criterio pasa a «Falta prueba».
