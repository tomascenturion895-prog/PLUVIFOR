# Estimación rotulada de días sin dato

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-93. Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia.

## Qué es

Un valor `estimado` para un día sin dato, calculado con estaciones vecinas del mismo tipo y corte, o con CHIRPS si ya está cargado. Se guarda aparte (`gap_estimates`).

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Da una referencia para días sin medición sin esconder que son huecos: el día sigue siendo «sin dato» en lo observado y el estimado se muestra rotulado y separado, con su método y sus vecinas.

## Qué no incluye

- No rellena ni modifica la serie observada, ni entra en acumulados.
- No inventa: sin base para estimar, el día queda sin dato. Hoy da 0 días estimados con los datos reales.
- Los parámetros (25 km, potencia 2) son una propuesta sin validar.
- No es una predicción hacia adelante.

## Dónde está

docs/datos/estimacion-huecos.md
