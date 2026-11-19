"""Servidor MCP de solo lectura sobre la API de PLUVIFOR (SCRUM-91).

Deja que una IA consulte la lluvia usando únicamente la API pública de consultas. No tiene
ninguna herramienta que escriba y no toca la base: todo lo que sabe lo pregunta por HTTP GET.
Se escribió con la biblioteca estándar (protocolo MCP por stdio) para no sumar dependencias.

PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial.
"""

VERSION = "0.1.0"
LEYENDA = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"
