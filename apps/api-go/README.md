# API en Go

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Puerta de entrada de la API de PLUVIFOR. El reparto del stack: **esta API en Go** sirve las consultas con rapidez, y **Python (FastAPI, en `apps/backend`)** hace el procesamiento de datos, la importación y la parte de predicción con IA. El contrato que une las dos partes está en `openapi.yaml`.

## Estado real

Es un **esqueleto**. Hoy implementa:

- `GET /health` (estado, versión, entorno y fecha de corte).
- El formato único de errores `{"error": {"code", "message"}}`, en español y sin detalles internos (404, 405 y fallos inesperados).
- Lectura de la configuración del entorno (`APP_ENV`, `API_GO_PORT`, `DATA_CUTOFF_DATE`, `DATABASE_URL`). De `DATABASE_URL` solo se toma el motor (SQLite o PostgreSQL); la URL, que puede llevar la clave, nunca se guarda ni se imprime.

**Todavía no** hay conexión a la base ni las rutas de estaciones y lluvia: esas siguen respondiendo desde Python. Para sumarlas hace falta elegir un driver de base de datos, y esa decisión queda para el equipo (ver abajo).

## Requisitos

Go 1.24 o superior (<https://go.dev/dl/>). Solo biblioteca estándar: no hay dependencias.

## Correr y probar

Desde `apps/api-go`:

```bash
go run ./cmd/api              # http://localhost:8080/health   (puerto: API_GO_PORT)
go vet ./...
go test ./...
gofmt -l .                    # no debe listar ningún archivo
```

## Estructura

```
cmd/api/             arranque del servidor
internal/config/     configuración del entorno (sin secretos)
internal/apierror/   formato único de errores
internal/httpapi/    rutas, 404/405 en JSON y recuperación de fallos
openapi.yaml         contrato (health implementado; estaciones y lluvia como referencia)
```

## Decisión pendiente: driver de base de datos

No se agregó ninguno: el equipo no lo acordó y desde el entorno de desarrollo no se pueden bajar módulos de Go. Opciones a evaluar antes de implementar las rutas de lectura:

| Opción | Motor | Ventaja | Costo |
|---|---|---|---|
| `modernc.org/sqlite` | SQLite | Go puro, sin compilador de C | Dependencia grande |
| `github.com/mattn/go-sqlite3` | SQLite | Muy usado | Requiere cgo |
| `github.com/jackc/pgx/v5` | PostgreSQL | Estándar de facto | Solo si se migra a PostgreSQL |

Recomendación: `modernc.org/sqlite` para la demo (misma base SQLite que usa Python). Cualquier driver se justifica en el PR que lo agregue.
