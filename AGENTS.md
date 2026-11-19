# PLUVIFOR · contexto para asistentes de IA

> Este archivo es la **fuente de verdad** para cualquier asistente de IA que trabaje en este repositorio (Claude, Gemini en Antigravity, opencode u otro). Leelo completo antes de escribir código. Si algo de lo que te piden contradice este archivo, avisá en lugar de hacerlo.

## Qué es el proyecto

**PLUVIFOR** (Pluviometría Integrada de Formosa) es un prototipo web de **reporte pluvial provincial**. Responde: ¿cuánto llovió, dónde y en qué período?, mostrando siempre la calidad del dato. Es el **Desafío 2 · Reporte pluvial** de la *Operación Agua* (AI LAB «Misión: Código Formosa», El Niño 2026/27), del Equipo 5 **SpaidyCode** (UTN, Extensión Áulica Formosa).

Leyenda obligatoria, siempre visible en la interfaz y en los documentos:

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

## Reglas que no se rompen

1. **Un hueco no es 0 mm.** Un día sin dato se guarda, se devuelve y se muestra como «sin dato», nunca como `0`. Distinguir tres estados: `dato`, `sin_fila` (el día no existe en la fuente) y `fila_sin_valor` (el día existe pero sin valor).
2. **Observado, referencia y estimado van separados**, nunca se suman ni se promedian entre sí. Categorías: `observado`, `referencia`, `simulado`/`estimado`.
3. **Fecha de corte de los datos: 31/10/2026.** No se usan datos posteriores.
4. **Todo dato lleva su fuente y su categoría.**
5. **No se inventa nada:** ni datos, ni coordenadas, ni endpoints, ni dependencias. Si falta algo, se deja vacío, se marca como pendiente y se pregunta.
6. **Horarios de corte distintos entre redes.** El «día» de lluvia no es igual en todas: red provincial, UPCA y SNIH 07:00–07:00; SMN e INTA convencional 09:00 (12–12 UTC). Al comparar redes, se advierte.
7. **Seis advertencias de comparabilidad:** horario de corte distinto, observado vs. estimado, cobertura despareja, dato sin validar, racha de ceros de 60 días o más, e inconsistencia con estaciones vecinas.

## Alcance

**Sí:** consultar y comparar lluvia por estación, zona y período; calidad del dato; mapa provincial; importación con auditoría; parte pluvial; eventos intensos (≥50 y ≥100 mm) y racha seca de forma **descriptiva**.

**Requiere fundamento (antes eran «No»):** alturas de ríos y riachos, caudales, predicción de afectaciones, zonas de riesgo, evacuaciones, atajaderos, capas de catastro de parcelas, y cualquier otro tema que no sea el núcleo de lluvia.

Según lo informado al equipo el 18/11/2026, se puede abarcar más y no importa pisar el trabajo de otros desafíos, **siempre que se fundamente** (indicación recibida de palabra; falta confirmarla por escrito). Antes de agregar algo de esta lista:

1. Escribí en el PR, en el campo «Por qué suma a la solución», cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?, o a decidir mejor con ese dato.
2. Si la decisión es grande, dejala anotada en `docs/`.
3. El núcleo de lluvia y su calidad van primero: no se deja nada del núcleo a medias por sumar un tema nuevo.
4. Las reglas de integridad del dato de arriba valen igual para todo lo que se agregue. Un tema nuevo no las relaja.

## Stack

| Parte | Tecnología |
|---|---|
| API (consultas) | Go 1.24 en `apps/api-go`, solo biblioteca estándar por ahora. Decisión del 19/11/2026: va en Go por rapidez. Hoy responde `/health` y **reenvía `/api/*` al backend en Python** (`BACKEND_URL`) con el mismo contrato; el contrato está en `apps/api-go/openapi.yaml`. Todavía no tiene driver de base de datos (decisión pendiente) |
| Procesamiento (datos, importación, IA) | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, SQLite (PostgreSQL/PostGIS por `DATABASE_URL`), pytest, ruff, en `apps/backend`. Hoy responde **todas** las rutas `/api/*` reales |
| Frontend | React 19 + TypeScript + Vite, React Router, Recharts, Leaflet, Vitest + Testing Library, Oxlint + Prettier |
| Capas geográficas | GeoJSON del IGN dentro del repositorio |
| CI | GitHub Actions |

## Estructura

```
apps/api-go/      API en Go (esqueleto: /health, errores, contrato OpenAPI)
apps/backend/     Procesamiento y API de datos (FastAPI)
apps/frontend/    Interfaz web (React + Vite)
docs/             Documentación, datos y QA
.github/          Plantilla de PR y flujos de CI
```

## Comandos

API en Go (desde `apps/api-go`):

```
go run ./cmd/api                                       # http://localhost:8080/health
go vet ./... && go test ./...
gofmt -l .                                             # no debe listar ningún archivo
```

Backend en Python (desde `apps/backend`):

```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload                          # http://localhost:8000/docs
pytest
ruff check . && ruff format --check .
```

Frontend (desde `apps/frontend`):

```
npm ci
npm run dev        # http://localhost:5173
npm test
npm run lint && npm run format:check
npm run build
```

## Reparto entre Go y Python

- **Go** (`apps/api-go`): puerta de entrada de las consultas. Mismo formato de errores `{"error": {"code", "message"}}` y mismas reglas que Python; el contrato es `openapi.yaml`.
- **Python** (`apps/backend`): reglas de calidad, importación, procesamiento y predicción con IA. Mientras Go no implemente una ruta, esa ruta responde desde Python.
- Las reglas de integridad del dato valen igual en las dos partes. Las dos leen la misma base (`DATABASE_URL`).
- Nada de dependencias nuevas sin acordarlo, tampoco en Go: el driver de base de datos está pendiente de decisión.

## Cómo trabajar

- Las reglas de ramas, commits y Pull Requests están en `docs/CONTRIBUTING.md`. Una rama por tarea de Jira: `feature/SCRUM-<n>-descripcion`.
- Commits en el formato `tipo: descripción (SCRUM-n)`.
- Hace falta un test para toda lógica nueva: como mínimo el caso feliz y uno de entrada inválida.
- Cambios chicos y enfocados en una tarea. No refactorices ni cambies archivos ajenos a la tarea.
- **Seguridad:** nunca escribas claves, tokens ni contraseñas en el código ni en commits. Las variables van en `.env` (ignorado por Git); el ejemplo está en `.env.example`. Valida toda entrada del usuario; usa el ORM, no SQL armado con texto.
- Textos de la interfaz y mensajes de error en **español**. Código, nombres de variables y rutas de la API en inglés.

## Datos de referencia

- Series del SIGA/INTA (estaciones 51, 424 y 425) procesadas en `docs/datos/`.
- Caso de demostración: la estación 424 marca 0 mm durante 281 días seguidos (2015-09-20 a 2016-06-26) mientras la 425 registra 1.265 mm en el mismo período. Es el ejemplo de por qué un cero prolongado se advierte y no se da por bueno.
- Las coordenadas de varias estaciones siguen pendientes: no las inventes.
