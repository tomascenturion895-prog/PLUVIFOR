# Estimación rotulada de días sin dato (SCRUM-93)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Un día sin dato **sigue siendo «sin dato»**. Esta función no lo rellena en la serie observada: guarda aparte, en la tabla `gap_estimates`, un valor **estimado** con su método y las estaciones que usó. Esos valores no entran en ningún acumulado, promedio ni comparación de lo observado.

## Qué se garantiza

- Categoría siempre `estimado` (lo exige una restricción de la tabla). Nunca se mezcla con `observado` ni con `referencia`.
- Solo cubre días `sin_fila` o `fila_sin_valor` (también lo exige la tabla): no pisa un dato medido.
- Solo dentro del período con datos medidos de esa estación; no se extrapola antes de la primera ni después de la última lectura.
- No pasa de la fecha de corte (31/10/2026).
- Es un dato derivado: se regenera (`estimate-gaps`) y repetir la corrida no duplica nada.
- Si no hay base para estimar, el día queda sin dato. No se inventa un cero.

## Métodos (en orden)

1. **`vecinas_idw_v1`**: promedio de la lluvia del mismo día en estaciones vecinas, ponderado por 1 / distancia². Una vecina cuenta solo si:
   - tiene coordenadas **verificadas** (las pendientes nunca se usan);
   - está a 25 km o menos;
   - es del **mismo tipo** y tiene el **mismo corte del día** que la estación con el hueco;
   - midió ese día (`dato`), y ese día no tiene una advertencia de calidad.
2. **`chirps_v3_punto`**: valor de CHIRPS en el punto de la estación, **solo si ya está cargado** como `estimado`. Esta función no descarga nada.

Cada fila guarda `method` y `detail` (vecinas, distancias, valores y parámetros usados).

**Los parámetros (25 km, potencia 2, mínimo 1 vecina) son una propuesta del equipo y no están validados.** Decisiones a confirmar: esos parámetros, el orden entre vecinas y CHIRPS, y la regla de «mismo tipo y mismo corte».

## Por qué se exige el mismo tipo y el mismo corte

Probamos el método con los datos reales: las dos estaciones de El Colorado (4,5 km entre sí), la convencional del INTA (EMC) y la automática de la EEA. Con `docs/datos/validar_estimacion.py`:

| Desfase entre las series | Correlación | Días en común |
|---|---|---|
| −1 día | **0,80** | 569 |
| mismo día | **0,10** | 570 |
| +1 día | −0,02 | 571 |

Con el pareo del mismo día, el error medio era de 6,73 mm sobre 1.140 comparaciones y la correlación de 0,10: **ruido**. Las dos estaciones están a 4,5 km y llueven casi lo mismo, pero **cuentan el «día» distinto** y las series quedan corridas un día. Por eso el método no compara estaciones de distinto tipo o corte (`mismo_horario`).

## Resultado hoy con los datos reales

**0 días estimados.** Las únicas estaciones cercanas son de distinto tipo, así que ninguna es una vecina válida, y todavía no hay CHIRPS cargado. Es el resultado correcto: sin una base honesta, el hueco se queda como hueco.

## Límites

- No se probó el método con un par de estaciones del mismo tipo y corte, porque hoy no hay ninguno con coordenadas verificadas a 25 km. Hasta tenerlo, el método no tiene una medida de error propia.
- Una lluvia local fuerte (tormenta aislada) puede no llegar a la vecina: la estimación puede quedar muy por debajo.
- Faltan las coordenadas de varias estaciones: no se inventan.

## Uso

```
python -m app.cli estimate-gaps --from 2013-01-01 --to 2026-10-31 [--station-id N] [--dry-run]
```

Lectura: `GET /api/estimates?station_id=N&from=AAAA-MM-DD&to=AAAA-MM-DD` (pública). En la pantalla **Estación** aparece en «Días sin dato con valor estimado», separada de la serie.
