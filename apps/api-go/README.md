# API en Go

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Puerta de entrada de la API de PLUVIFOR. El reparto del stack: **esta API en Go** sirve las consultas con rapidez, y **Python (FastAPI, en `apps/backend`)** hace el procesamiento de datos, la importación y la parte de predicción con IA. El contrato que une las dos partes está en `openapi.yaml`.

## Estado real

Es la **puerta de entrada**. Hoy:

- `GET /health` lo responde Go (estado, versión, entorno y fecha de corte).
- **Todo lo que empieza con `/api/` lo reenvía al backend en Python** (`BACKEND_URL`, por defecto `http://127.0.0.1:8000`) sin cambiar nada: mismo estado, mismo cuerpo, mismos encabezados y la misma clave de administración. Se comprobó que estaciones, series, acumulados, comparador y errores dan exactamente lo mismo por Go que directo a Python. Si el backend no está, Go responde 502 en español (sin mostrar su dirección); si tarda, 504; un cuerpo de más de 6 MiB, 413.
- Una ruta propia de Go gana sobre el reenvío. Ya están escritas `GET /api/stations`, `GET /api/stations/{id}` (SCRUM-84) y `GET /api/rainfall` (SCRUM-85), y además `GET /api/events` (SCRUM-63, solo existe en Go: días de 50 y 100 mm y rachas secas, descriptivo; un hueco corta la racha y no cuenta como seco; sin el driver de SQLite responde 404), con los mismos filtros, límites, errores y reglas del dato que Python (un hueco es `mm: null`, nunca 0; corte 31/10/2026; máximo 3.660 días). Las atiende Go leyendo la base en solo lectura (`internal/sqlstore`) cuando el programa se compila con el driver de SQLite (`-tags sqlite`); sin driver, arranca igual y las reenvía a Python.
- El formato único de errores `{"error": {"code", "message"}}`, en español y sin detalles internos (404, 405 y fallos inesperados).
- Lectura de la configuración del entorno (`APP_ENV`, `API_GO_PORT`, `DATA_CUTOFF_DATE`, `DATABASE_URL`, `BACKEND_URL`). De `DATABASE_URL` solo se toma el motor (SQLite o PostgreSQL); la URL, que puede llevar la clave, nunca se guarda ni se imprime.

**Reparto:** Python procesa e importa los datos y escribe en la base; Go atiende las consultas leyendo la misma base en solo lectura. Hoy Go atiende estaciones y la serie diaria; el comparador, los acumulados, el parte, la importación, la salud de la red y los reportes de campo los sigue respondiendo Python por el reenvío, hasta que se porten (uno por vez, con paridad).

Go también limita los pedidos por cliente (`API_GO_RATE_LIMIT_PER_MINUTE`, 120 por defecto; la importación, 10) y pone los mismos encabezados de seguridad que Python.

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
internal/sqlstore/   lectura de la base (database/sql, solo lectura); el driver va aparte
internal/ratelimit/  límite de pedidos por cliente
internal/secheaders/ encabezados de seguridad, los mismos que Python
internal/rainfall/   serie diaria: calendario con huecos, resumen, cobertura y advertencias
testdata/parity/     base de demostración y respuestas de Python para las pruebas de paridad
openapi.yaml         contrato (health, estaciones y serie diaria implementados en Go)
```

## Driver de base de datos (SQLite)

El adaptador `internal/sqlstore` usa solo `database/sql`; el driver se elige en un único archivo, `internal/sqlstore/driver_sqlite.go`, que se compila con `-tags sqlite`. Elegido: **`github.com/ncruces/go-sqlite3`** v0.25.0 (SQLite en Go puro, sin cgo; trae `wazero` y `golang.org/x/sys`). Es el que se pudo verificar de punta a punta desde el entorno de desarrollo; `modernc.org/sqlite` es una alternativa equivalente (cambia solo ese archivo).

**Falta un paso desde una máquina con acceso normal a los módulos de Go** (el entorno de desarrollo solo llega a GitHub y no puede generar un `go.sum` verificable):

```
cd apps/api-go
go get github.com/ncruces/go-sqlite3@v0.25.0
go mod tidy
go test -tags sqlite ./...            # incluye las 47 consultas de paridad contra una base SQLite real
go build -tags sqlite -o api ./cmd/api
```

Después, commitear `go.mod` y `go.sum`: el CI detecta el driver en `go.sum` y corre también las pruebas con `-tags sqlite`. Sin driver, `go test ./...` y `go run ./cmd/api` siguen funcionando (Go reenvía todo a Python).

Go lee el `.env` (de la carpeta actual o de las tres de arriba; lo que ya esté en el entorno gana) y encuentra solo la base que crea Python: una ruta relativa como `./pluvifor.db` se busca desde donde corre Go y después en `apps/backend`. Para correrlo con otra base en Linux o Mac: `DATABASE_URL=sqlite:////ruta/absoluta/pluvifor.db go run -tags sqlite ./cmd/api`. En PowerShell: `$env:DATABASE_URL = "sqlite:///C:/ruta/real/pluvifor.db"` y después `go run -tags sqlite ./cmd/api` (tiene que ser una ruta que exista: si no se puede abrir la base, Go avisa y reenvía a Python). Go escucha solo en `127.0.0.1` (`API_GO_HOST`; con `0.0.0.0` queda abierto a la red local). Usá ruta absoluta: una ruta relativa se resuelve desde donde corre Go, no desde donde corre Python. Go abre la base en solo lectura (`mode=ro`). PostgreSQL todavía no: con `DATABASE_URL` de PostgreSQL, Go reenvía a Python.

Medición del 19/11 con la base de demostración (una conexión; 8 conexiones en paralelo): serie de 281 días 3,5 ms contra 5,8 ms de Python (494 contra 117 pedidos por segundo); catálogo 0,8 ms contra 3,1 ms (2.514 contra 305); ficha 0,5 ms contra 2,6 ms (4.153 contra 389). Con límites de pedidos desactivados en los dos y todas las respuestas en 200. Es una medición chica en una máquina de desarrollo, no una prueba de carga.

## Pruebas de paridad con Python

`testdata/parity/generate.py` vuelca la base de demostración (`db.json`) y guarda lo que responde hoy la API de Python a 47 consultas (`cases.json`): catálogo con cada filtro, ficha, serie con huecos, recorte al corte, categorías, errores 404 y 422. `internal/httpapi/parity_test.go` carga esa base en un lector de memoria y `sqlstore_parity_test.go` (con `-tags sqlite`) en una base SQLite real; las dos exigen el mismo estado y el mismo JSON (por valor: `0` y `0.0` son el mismo número). Para regenerar, desde `apps/backend` con el entorno de Python activo: `python ../api-go/testdata/parity/generate.py`.

Diferencias conocidas y aceptadas: (1) en un 422 por fecha mal formada se exige el mismo código y el mismo parámetro, no la misma frase en inglés de pydantic; (2) Go acepta fechas solo como `AAAA-MM-DD`, Python además acepta fecha y hora; (3) en la búsqueda por texto, Go pasa el texto buscado a minúsculas con todo Unicode y SQLite solo pasa ASCII en las columnas (con PostgreSQL coinciden); además `%` y `_` en `q` funcionan como comodines, igual que en Python.
