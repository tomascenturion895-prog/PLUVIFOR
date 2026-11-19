# Servidor MCP de solo lectura

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Permite que una IA (por ejemplo Claude) consulte la lluvia de Formosa **usando solo la API de PLUVIFOR**, y que siempre reciba el estado, la fuente, la categoría y las advertencias de cada dato. Es la tarea SCRUM-91.

## Por qué suma a la solución

Responde «¿cuánto llovió, dónde y en qué período?» a quien pregunta en lenguaje natural, sin saltarse las reglas de calidad: un día sin dato se dice «sin dato», nunca 0 mm, y las advertencias de comparabilidad viajan con la respuesta.

## Qué garantiza

1. **No puede escribir.** Hay cuatro herramientas y las cuatro son consultas (`readOnlyHint: true`). El lector de la API (`servidor_mcp/api.py`) solo tiene un método, `get`: aunque alguien agregue una herramienta nueva, no tiene con qué hacer un `POST`. No toca la base de datos ni la clave de administración: todo lo pide por HTTP `GET` a las rutas públicas.
2. **Un hueco no es 0 mm.** A cada `mm` se le suma su lectura en texto (`mm_texto`): `sin dato` cuando es `null`, y `0 mm` solo cuando hubo una medición de cero. No se cambia ningún número. Cada respuesta trae además la leyenda de prototipo y una nota que lo aclara.
3. **Estado, fuente, categoría y advertencias** salen tal cual de la API. Observado, referencia y estimado no se mezclan: la categoría es un argumento explícito (por defecto, `observado`).
4. **Corte de datos 31/10/2026:** lo aplica la API; el servidor no lo salta.
5. **Argumentos validados** antes de consultar (fechas reales, ids enteros, categoría conocida, sin argumentos desconocidos). Los errores salen en español y sin detalles internos.

## Herramientas

| Herramienta | Qué hace | Ruta de la API |
|---|---|---|
| `listar_estaciones` | Catálogo con fuente, red y estado de coordenadas. Filtros: texto, zona, departamento, fuente. | `GET /api/stations` |
| `lluvia_por_estacion` | Serie diaria de una estación en un período, con estado, fuente, banderas y advertencias. | `GET /api/rainfall` |
| `acumulado` | Acumulado por estación (no se suman entre estaciones) de la red, una estación o una zona. Sin ningún dato: «sin dato». No trae advertencias de calidad. | `GET /api/rainfall/accumulated` |
| `comparar_estaciones` | Compara series y devuelve las advertencias de comparabilidad (horario de corte, observado vs. estimado, cobertura, sin validar, racha de ceros, inconsistencia con vecinas). | `GET /api/rainfall/compare` |

Preguntas que sirven de ejemplo: «¿Qué estaciones hay en El Colorado?», «¿Cuánto llovió en la estación 2 entre el 20/9/2015 y el 26/6/2016?», «Compará las estaciones 2 y 3 en ese período y decime qué advertencias hay».

## Cómo conectarlo

Necesita la API levantada (Go en `http://localhost:8080` o Python en `http://localhost:8000`; ver `docs/ENTORNO.md`) y el entorno del backend instalado (`pip install -r requirements.txt`). No suma dependencias nuevas: habla el protocolo MCP con la biblioteca estándar.

**Probarlo a mano** (desde `apps/backend`, con el entorno virtual activo):

```bash
python -m servidor_mcp --api-url http://localhost:8080
```

Queda esperando mensajes por la entrada estándar (un JSON por línea); se corta con Ctrl+C. La dirección también puede venir de la variable `PLUVIFOR_API_URL`.

**Desde un cliente MCP por stdio** (Claude Desktop, Claude Code u otro), con el formato habitual `mcpServers`. Usá la ruta real del Python del entorno virtual y de `apps/backend` (en Windows, con `\\` dobles en JSON):

```json
{
  "mcpServers": {
    "pluvifor": {
      "command": "C:\\ruta\\al\\repo\\apps\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "servidor_mcp", "--api-url", "http://localhost:8080"],
      "env": { "PYTHONPATH": "C:\\ruta\\al\\repo\\apps\\backend" }
    }
  }
}
```

Con Claude Code: `claude mcp add pluvifor --env PYTHONPATH=<ruta>/apps/backend -- <python> -m servidor_mcp`.

> **Lo que se probó y lo que no:** el protocolo se probó con 41 pruebas automáticas y con un cliente de prueba por stdio contra la API real y la base de demo (`initialize`, `tools/list` y las cuatro herramientas). **No se probó con Claude Desktop ni con otro cliente real**: la configuración de arriba sigue el formato estándar, pero conviene confirmarla en la máquina donde se use.

## Decisiones

- **Sin el SDK oficial de MCP.** Sumarlo era una dependencia nueva y el protocolo de herramientas por stdio es chico (`initialize`, `ping`, `tools/list`, `tools/call`). Si el equipo prefiere el SDK, la lógica (`herramientas.py`, `api.py`) no cambia: solo se reemplaza `servidor.py`.
- **La carpeta se llama `servidor_mcp` y no `mcp`** (como proponía la tarea) para no tapar al paquete oficial `mcp` si algún día se instala.
- **Entra por la API, no por la base.** Así hereda las reglas de calidad, el corte y los límites de pedidos que ya tiene la API.

## Qué no hace

No importa, no carga ni corrige datos; no lee reportes de campo ni lecturas de sensores simulados; no tiene recursos ni prompts MCP; no autentica (las rutas de lectura son públicas). No predice ni evalúa riesgo: describe lo que dice la API.
