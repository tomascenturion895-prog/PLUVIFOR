# Casos de prueba con datos reales del SIGA

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-42. Cada caso usa filas reales de `docs/datos/lluvia_diaria_siga_formosa.csv`, sin modificar, y tiene su resultado esperado. Las pruebas están en `apps/backend/tests/test_casos_reales.py` y cargan `apps/backend/tests/fixtures/siga_casos_reales.csv` (654 filas, las ventanas de abajo) y `siga_estaciones.csv` (copia de `docs/datos/estaciones_siga_formosa.csv`).

**Cómo se calcularon los valores esperados:** leyendo el CSV completo con el módulo `csv` de Python, sin usar código de la aplicación, y comparando después con lo que devuelve la API. Coincidieron todos en el primer intento.

Códigos de estación: 51 = INTA El Colorado (EMC, convencional), 424 = El Colorado EEA (automática), 425 = Bartolomé de las Casas.

## Los casos

| # | Caso | Pedido a la API | Resultado esperado |
|---|---|---|---|
| 1 | Racha de ceros de la 424 | 424, 2015-09-20 a 2016-06-26 | 281 días, los 281 con dato, acumulado 0 mm; advertencia `ceros_prolongados` del 2015-09-20 al 2016-06-26 |
| 2 | La 425 en el mismo período | 425, 2015-09-20 a 2016-06-26 | 281 días con dato, **1.265 mm**; sin `ceros_prolongados` |
| 3 | El hueco corta la racha | 424, 2016-06-27 a 2016-06-28 | 2 días `fila_sin_valor`, 0 con dato, acumulado **sin dato** (no 0); sin `ceros_prolongados` |
| 4 | Sin fila y sin valor, por separado | 425, 2018-05-01 a 2018-05-15 | 15 días: 3 con dato, 11 `sin_fila`, 1 `fila_sin_valor`; cobertura 0,2; acumulado 0 mm; advertencia `cobertura_baja` |
| 5 | Un mes de filas sin valor | 51, 2014-08-15 a 2014-09-20 | 37 días: 8 con dato (115,5 mm) y 29 `fila_sin_valor`; cobertura 0,2162 |
| 6 | Mismo evento, un día de diferencia entre redes | 51 y 424, días 2014-04-10 y 2014-04-11 | 424: 138 mm el 10/04 y 11,75 mm el 11/04. 51: 0 mm el 10/04 y 143 mm el 11/04 |
| 6b | La semana completa tampoco coincide | 51 y 424, 2014-04-08 a 2014-04-13 | 51: 159 mm. 424: 153,25 mm |
| 7 | Período que pasa el corte | 424, 2017-01-01 a 2026-12-31 | Se recorta al 2026-10-31 (3.591 días), se avisa el recorte y el acumulado es sin dato |
| 7b | Período de más de 10 años | 424, 2016-06-20 a 2026-12-31 | Se rechaza con 422 `range_too_large` (3.817 días contra un máximo de 3.660) |
| 8 | Período posterior al corte | 424, 2026-11-01 a 2026-11-30 | 422 `after_cutoff` |
| 9 | Acumulado por estación | `/api/rainfall/accumulated`, 424, mismo período del caso 1 | 0 mm, 281 días con dato y la advertencia `ceros_prolongados` |

## De dónde salen las ventanas del archivo de prueba

| Estación | Desde | Hasta | Para qué caso |
|---|---|---|---|
| 424 y 425 | 2015-09-15 | 2016-07-05 | 1, 2, 3 |
| 51 y 424 | 2014-04-08 | 2014-04-13 | 6, 6b |
| 51 | 2014-08-15 | 2014-09-20 | 5 |
| 425 | 2018-05-01 | 2018-05-15 | 4 |

Los casos 7, 7b y 8 trabajan sobre las mismas filas: lo que cae fuera de las ventanas figura como `sin_fila`, igual que cualquier día que no está cargado.

## Lo que se vio al armarlos

- **El máximo de 3.660 días se aplica antes de recortar al 31/10.** Un pedido de 2016-06-20 a 2026-12-31 se rechaza aunque el recorte lo dejaría en 3.786 días. Es el comportamiento actual y el caso 7b lo fija. Si se quiere que se recorte primero, es una decisión del equipo.
- **Los datos del SIGA no llegan al 31/10/2026:** el último día cargado es el 2023-03-24 (425), el 2022-12-07 (424) y el 2015-06-28 (51). Por eso el caso 7 no tiene datos que recortar y comprueba el recorte y el «sin dato».
- **El acumulado de un período sin ningún dato es sin dato**, no 0 mm (casos 3 y 7). Un período con días de 0 mm informados sí da 0 (caso 1).
- No se probó la diferencia entre `mm_pluviometrica` y `mm_cronologica`: la API hoy usa solo la pluviométrica.
- Estos casos no verifican las advertencias de comparación entre redes (horario de corte distinto) porque la comparación de estaciones (SCRUM-36) todavía no está entregada.
