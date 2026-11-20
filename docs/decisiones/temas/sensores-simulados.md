# Ingesta de sensores simulados

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-94. Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia.

## Qué es

Un contrato de ingesta (`POST /api/sensor-readings`, con clave de dispositivo), un simulador y una pantalla de lecturas. Todo lo que entra es `simulado` y se rotula así.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Deja listo el camino por donde entraría la lluvia de equipos automáticos, con idempotencia y el día contado con el corte de Argentina, sin esperar el equipo. Ayuda a decidir mejor al mostrar cómo se verían esas lecturas **separadas** de lo medido.

## Qué no incluye

- No hay sensores reales: ni equipo, ni comunicación definidos.
- Una lectura simulada no se suma ni se promedia con lo observado.
- No se usa para acumulados observados.

## Dónde está

docs/ingesta-sensores.md
