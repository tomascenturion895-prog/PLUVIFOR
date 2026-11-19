# SMN · Estadísticas Climatológicas Normales 1991-2020

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Fuente de la **normal mensual de lluvia** (SCRUM-60). Es una **referencia**, no un dato observado: nunca se suma ni se promedia con lo observado.

| Dato | Valor |
|---|---|
| Organismo | Servicio Meteorológico Nacional (SMN) |
| Publicación | *Estadísticas Climatológicas Normales: República Argentina, período 1991-2020*, SMN, 2023, 847 pp., ISSN 2953-5549 |
| Dónde | Repositorio institucional del SMN: https://repositorio.smn.gob.ar/handle/20.500.12160/2506 |
| Licencia | Creative Commons Reconocimiento 2.5 Argentina (la indica el repositorio) |
| Estación usada | **Formosa Aero** (WIGOS 0-20000-0-87162), lat 26,21242 S, lon 58,22929 O, altura 59 m |
| Tabla | «Precipitación (mm)», fila «Promedio», página impresa 400 |
| Se consultó | 19/11/2026 |

## Valores cargados (mm)

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic | Anual publicado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 163,5 | 135,6 | 138,2 | 159,6 | 110,1 | 60,3 | 41,0 | 34,8 | 74,8 | 150,3 | 159,9 | 178,4 | 1406,4 |

Control: la suma de los 12 meses da 1406,5 mm y la publicación informa 1406,4 mm (diferencia de redondeo).

Archivo: `docs/datos/normales_smn_formosa_aero_1991_2020.csv`. Se carga con `python -m app.cli import-normals` y se consulta en `GET /api/climate-reference?station_id=…`.

## Límites que hay que tener presentes

- **Es una sola estación y está en la ciudad de Formosa.** No representa el clima de toda la provincia: la lluvia cambia mucho de este a oeste. Comparar una estación del oeste (por ejemplo, las del INTA) con esta normal puede inducir a error. No se interpoló ni se extendió a otras estaciones.
- Es la normal 1991-2020 (30 años). La publicación del SMN trae otras estaciones del país, pero no se cargaron: solo se cargó la que está en Formosa.
- Los datos observados de las estaciones del proyecto vienen de otra red (SIGA/INTA, día de lluvia 09:00 según su fuente) y no se cargaron como normal.
- Los valores se copiaron a mano de la tabla del PDF. Quien entregue el proyecto debería re-verificar al menos dos meses contra el original.
- No se agregaron normales de la red provincial ni de las estaciones del INA: no hay fuente verificada para ellas.
