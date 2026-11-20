# Pitch de 3 minutos y 5 diapositivas (SCRUM-75)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Guion del pitch de **PLUVIFOR** (Equipo 5 SpaidyCode, Desafío 2 · Reporte pluvial). Solo usa cifras que están en el repositorio (`docs/datos/`, `README.md`).

**Estado:** borrador para que Tomás revise. **Pendiente:** cronometrar con el equipo (el tiempo de abajo es una estimación por cantidad de palabras, no una medición) y asignar quién dice cada parte (ver tabla de responsables).

## Guion (objetivo: 2:50 como máximo)

| # | Diapositiva | Tiempo | Qué se dice | Responsable |
|---|---|---|---|---|
| 1 | **El problema** | 0:00 – 0:30 | «Con El Niño, la lluvia cambia según la zona y cada productor necesita saber cuánto llovió, dónde y desde cuándo. Hoy ese dato está repartido entre redes con horarios de corte distintos, huecos y estaciones que dejan de informar sin avisar.» | [pendiente] |
| 2 | **La solución: PLUVIFOR** | 0:30 – 1:00 | «PLUVIFOR reúne las series de lluvia y permite consultarlas por estación, zona y período, siempre mostrando la calidad del dato. Su regla central: un hueco no es 0 mm. Un día sin dato se muestra como “sin dato”.» | [pendiente] |
| 3 | **Demo: 424 contra 425** | 1:00 – 2:00 | «Mismo período, del 20/09/2015 al 26/06/2016. La estación 424 marca 0 mm durante 281 días seguidos. La 425, a pocos kilómetros, registra 1.265 mm. PLUVIFOR no da por bueno ese cero: lo advierte como racha de ceros prolongada. Mostramos el mapa, la ficha de la estación y el parte pluvial.» | [pendiente] |
| 4 | **Rigor y honestidad del dato** | 2:00 – 2:30 | «Observado, referencia y estimado van siempre separados. Cada dato lleva fuente y categoría. Hay seis advertencias de comparabilidad, y la fecha de corte es el 31/10/2026. Hoy hay series reales de 3 estaciones del SIGA/INTA (7.648 días); las demás fuentes están sin verificar y lo decimos.» | [pendiente] |
| 5 | **Siguientes pasos** | 2:30 – 2:50 | «Sumar la red provincial cuando se confirme su licencia, publicar la demo y seguir con la estimación de huecos sin mezclarla con lo medido. Es un prototipo, no una herramienta oficial.» | [pendiente] |

Cantidad aproximada: 330 palabras (≈ 2:20 a ritmo de 140 palabras por minuto, más la demo en pantalla).

## Notas para quien presenta

- Caso central: 424 contra 425 (`docs/datos/`). No agregar otras cifras que no estén en el repositorio.
- No decir «a pocos kilómetros» si no se confirma la distancia entre las estaciones: **las coordenadas de varias estaciones siguen pendientes**. Alternativa segura: «la estación 425, en el mismo período».
- No afirmar que la 424 «falló»: el sistema solo advierte que un cero tan largo no se da por bueno.
- Antes de la demo: `python -m app.cli reset-demo --yes` y levantar API y frontend (ver `README.md`).
- Si no hay internet, la demo corre local con datos incluidos en el repositorio.

## Hecho cuando (SCRUM-75)

- [x] Guion con problema, solución, demo, aporte y siguientes pasos.
- [x] 5 diapositivas definidas (títulos y contenido de arriba).
- [x] Caso 424 contra 425 como ejemplo central.
- [ ] Ensayado con cronómetro: dura 3 minutos o menos. **Lo tiene que hacer el equipo.**
