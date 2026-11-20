# Servidor MCP de solo lectura

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-91. Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia.

## Qué es

Cuatro herramientas que permiten que un asistente de IA consulte la API (estaciones, lluvia, acumulados y calidad) por HTTP `GET`.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Permite preguntar «¿cuánto llovió en tal estación y período?» desde un asistente y recibir la misma respuesta que la interfaz, con su fuente, su categoría y sus advertencias. Una consulta sin datos responde «sin dato», nunca 0.

## Qué no incluye

- No escribe: no tiene método para `POST` ni acceso a la base ni a la clave de administración.
- No interpreta ni predice: devuelve lo que devuelve la API.
- No se probó con un cliente MCP real, solo por stdio.

## Dónde está

docs/entrega/mcp.md
