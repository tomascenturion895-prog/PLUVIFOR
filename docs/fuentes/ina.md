# Fuente: INA (Alerta Hidrológico) · lluvia diaria en Formosa

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

**Resultado:** el INA **sí** tiene series de lluvia diaria de estaciones de Formosa. Se listaron **15 estaciones** en `docs/datos/ina_estaciones_formosa.csv`: 12 dentro de la provincia y 3 sobre el límite (el río Bermejo). Consultado el 18/11/2026. Tarea SCRUM-27.

**Qué se hizo y qué no.** Se consultó el listado de series y sus fechas; **no se descargaron valores de lluvia**. Falta bajar y revisar los datos antes de usarlos.

## Cómo se consultó

API del INA: `https://alerta.ina.gob.ar/a5` (la documentación general está en la aplicación web de datos hidrológicos del INA).

1. `obs/variables?format=json`: lista las 95 variables. Las de lluvia son 8; la que nos sirve es la **id 1, «precipitación diaria 12Z»** (el corte diario es a las 12 UTC, o sea 09:00 hora de Argentina). También hay horaria (id 31) y por intervalo nativo (id 27).
2. `obs/puntual/series?format=geojson&var_id=<id>&GeneralCategory=Climate`: lista las series de cada variable en todo el país (932 de lluvia diaria).
3. Se filtraron las que están en el recuadro de Formosa (lon −62,4 a −57,4; lat −27,2 a −22,4) y tienen datos. Resultaron 36 estaciones.
4. Se cruzó cada coordenada con el contorno de Formosa del IGN (simplificado a unos 300 m). La API no informa la provincia. Quedaron 13 dentro; se sumaron 2 sobre el río Bermejo, que el contorno simplificado deja afuera por centímetros. Las restantes caen en otras provincias o en Paraguay.

## Qué dice la lista

| Dato | Valor |
|---|---|
| Estaciones con lluvia diaria | 15 |
| Con serie horaria además | 5 (Laguna Yema, Ibarreta, Pirané, Posta Zalazar, Ingeniero Juárez) |
| Período más largo | 2019-07-14 a 2026-11-17 (las tres del río Bermejo) |
| Período más corto | desde 2025-11-26 (cinco estaciones: El Aybal, Pozo del Tigre, Belgrano, Guadalcazar y San Martín N°2), unas 350 filas |
| Última fecha de datos | 2026-11-17 en la mayoría |

El campo «disp» es el código de disponibilidad que devuelve la API (`NRT`, `RT`, `C`, `H`). No encontré documentado qué significa cada uno, así que está copiado tal cual y **no se debe interpretar** hasta confirmarlo con el INA.

## Cómo encaja con las reglas del proyecto

- **Fecha de corte:** las series llegan a noviembre de 2026. Al cargar hay que recortar al 31/10/2026.
- **Horario de corte:** la lluvia diaria del INA se corta a las 12 UTC, igual que el SMN y el INTA convencional. Al compararla con la red provincial, la UPCA o el SNIH (07:00 a 07:00) hay que mostrar la advertencia de horario distinto.
- **Categoría:** la variable figura como «observación de campo», así que sería `observado`. Confirmarlo al cargar.
- **Huecos:** no se sabe todavía si hay días sin fila o sin valor. Mismo tratamiento que el SIGA: un hueco no es 0 mm.
- **Estaciones del INTA en el INA:** el INA también lista estaciones de la red del INTA de la zona, por ejemplo «El Colorado EEA INTA», pero **sin datos** (disponibilidad `N`). Para el INTA seguimos usando el SIGA.

## Pendiente

1. **Condiciones de uso:** la página del INA que consulté no dice la licencia. Confirmarla antes de publicar los datos.
2. **Provincia de las 3 estaciones del Bermejo:** están sobre el límite; verificar a cuál pertenecen.
3. **Propietario de cada red** (RHN, RMA, RMET, etc.): no lo verifiqué para todas; completar antes de citarlas como fuente.
4. **Descargar y revisar valores** de al menos una estación con `getObservaciones` (tipo puntual, `series_id`, `timestart`, `timeend`) y contrastarla con otra red.
