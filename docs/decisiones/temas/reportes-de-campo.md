# Reportes de campo (lluvia anotada donde no hay estación)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-90. Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia.

## Qué es

Un formulario con clave de administración para cargar la lluvia que anota la policía donde no hay estación. Entra como `observado`, **sin validar**, con la ubicación pendiente si no se informó.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Hay estaciones sin mantenimiento y buena parte de la lluvia solo existe como anotación. Sin este canal, esos días serían huecos aunque llovió. Responde ¿cuánto llovió y dónde?, a costa de decir claramente que el dato no está validado (advertencia de dato sin validar).

## Qué no incluye

- No es una fuente policial automática: no hay una conexión con ninguna institución.
- No valida ni corrige el dato: lo rotula.
- No publica el nombre de quien reporta: el listado pide clave porque es un dato personal.
- No está en el mapa público (ver SCRUM-101).

## Dónde está

docs/modelo-datos.md (`field_reports`)
