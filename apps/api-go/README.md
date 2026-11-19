# API en Go

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Puerta de entrada de la API de PLUVIFOR. El reparto del stack: **esta API en Go** sirve las consultas con rapidez, y **Python (FastAPI, en `apps/backend`)** hace el procesamiento de datos, la importación y la parte de predicción con IA. El contrato que une las dos partes está en `openapi.yaml`.

## Estado real

Es la **puerta de entrada**. Hoy:

- `GET /health` lo responde Go (estado, versión, entorno y fecha de corte).
- **Todo lo que empieza con `/api/` lo reenvía al backend en Python** (`BACKEND_URL`, por defecto `http://127.0.0.1:8000`) sin cambiar nada: mismo estado, mismo cuerpo, mismos encabezados y la misma clave de administración. Se comprobó que estaciones, series, acumulados, comparador y errores dan exactamente lo mismo por Go que directo a Python. Si el backend no está, Go responde 502 en español (sin mostrar su dirección); si tarda, 504; un cuerpo de más de 6 MiB, 413.
- Una ruta propia de Go gana sobre el reenvío. Ya están escritas `GET /api/stations`, `GET /api/stations/{id}` (SCRUM-84) y `GET /api/rainfall` (SCRUM-85), con los mismos filtros, límites, errores y reglas del dato que Python (un hueco es `mm: null`, nunca 0; corte 31/10/2026; máximo 3.660 días). Se activan con `httpapi.WithStations` y `httpapi.WithRainfall` cuando exista un lector de la base.
- El formato único de errores `{"error": {"code", "message"}}`, en español y sin detalles internos (404, 405 y fallos inesperados).
- Lectura de la configuración del entorno (`APP_ENV`, `API_GO_PORT`, `DATA_CUTOFF_DATE`, `DATABASE_URL`, `BACKEND_URL`). De `DATABASE_URL` solo se toma el motor (SQLite o PostgreSQL); la URL, que puede llevar la clave, nunca se guarda ni se imprime.

**Todavía no** hay conexión a la base: `cmd/api` no inyecta ningún lector, así que hoy esas rutas las responde Python a través del reenvío. Conectarlas es un solo archivo (un adaptador que cumpla `station.Reader` y `rainfall.Reader`) más dos líneas en `cmd/api/main.go`, y espera la decisión del driver (ver abajo).

## Usarla con la interfaz

Con el backend en Python corriendo en el 8000, levantá Go (`go run ./cmd/api`, puerto 8080) y apuntá la interfaz a Go: `VITE_API_URL=http://localhost:8080 npm run dev` desde `apps/frontend`.

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
internal/proxy/      reenvío de /api/* al backend en Python
internal/civil/      fecha de calendario AAAA-MM-DD (el «día de lluvia» no es un instante)
internal/station/    catálogo de estaciones y la interfaz Reader (el consumidor la define)
internal/rainfall/   serie diaria: calendario con huecos, resumen, cobertura y advertencias
testdata/parity/     base de demostración y respuestas de Python para las pruebas de paridad
openapi.yaml         contrato (health, estaciones y serie diaria implementados en Go)
```

## Decisión pendiente: driver de base de datos

No se agregó ninguno: el equipo no lo acordó. Opciones a evaluar para conectar las rutas ya escritas:

| Opción | Motor | Ventaja | Costo |
|---|---|---|---|
| `modernc.org/sqlite` | SQLite | Go puro, sin compilador de C | Dependencia grande |
| `github.com/mattn/go-sqlite3` | SQLite | Muy usado | Requiere cgo |
| `github.com/jackc/pgx/v5` | PostgreSQL | Estándar de facto | Solo si se migra a PostgreSQL |

Recomendación: `modernc.org/sqlite` para la demo (misma base SQLite que usa Python). Cualquier driver se justifica en el PR que lo agregue.

Lo que se comprobó el 19/11 desde el entorno de desarrollo (que solo llega a GitHub): `modernc.org/sqlite` no se puede bajar ahí (su dirección no está permitida), y `github.com/ncruces/go-sqlite3` v0.25.0 (SQLite en Go puro, sin cgo) sí compila y abre una base, pero solo reemplazando `golang.org/x/sys` por su espejo de GitHub; sin acceso a `sum.golang.org` no se puede generar un `go.sum` verificable. Por eso el adaptador no se escribió acá: con la decisión tomada, se agrega desde una máquina con acceso normal a los módulos (`go get`, `go mod tidy`) y se justifica en su PR.

## Pruebas de paridad con Python

`testdata/parity/generate.py` vuelca la base de demostración (`db.json`) y guarda lo que responde hoy la API de Python a 47 consultas (`cases.json`): catálogo con cada filtro, ficha, serie con huecos, recorte al corte, categorías, errores 404 y 422. `internal/httpapi/parity_test.go` carga esa base en un lector de memoria y exige el mismo estado y el mismo JSON (por valor: `0` y `0.0` son el mismo número). Para regenerar, desde `apps/backend` con el entorno de Python activo: `python ../api-go/testdata/parity/generate.py`.

Diferencias conocidas y aceptadas: (1) en un 422 por fecha mal formada se exige el mismo código y el mismo parámetro, no la misma frase en inglés de pydantic; (2) Go acepta fechas solo como `AAAA-MM-DD`, Python además acepta fecha y hora; (3) en la búsqueda por texto, Go pasa a minúsculas todo Unicode y SQLite solo ASCII (con PostgreSQL coinciden).
