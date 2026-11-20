# Salud de la red de estaciones

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-89. Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia.

## Qué es

Una lectura que clasifica cada estación como activa, en silencio (30 días sin dato, umbral configurable) o sin datos, respecto de la fecha de corte.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Antes de confiar en un acumulado hay que saber si la estación informa. Un hueco por abandono no es lo mismo que un día sin lluvia: esta lectura lo hace visible y sostiene la regla «un hueco no es 0 mm».

## Qué no incluye

- No dice por qué una estación calló (sensor, comunicación, abandono).
- No avisa ni envía alertas a nadie.
- Mide contra el corte del 31/10/2026, no contra la fecha de hoy.

## Dónde está

GET /api/network/health; pantalla Salud de la red
