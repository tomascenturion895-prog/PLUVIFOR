# Entorno local

Cómo dejar tu computadora lista para trabajar en PLUVIFOR, desde cero. Sirve para las cinco personas del equipo y para cualquier herramienta de IA que uses.

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

## 1. Qué necesitás

| Herramienta | Versión | Para qué |
|---|---|---|
| Git | cualquiera reciente | Bajar y subir el código |
| Python | 3.12 o superior | Backend (API) |
| Node.js | 22 o superior (LTS) | Frontend, y el script de verificación |
| Go | 1.24 o superior | API en Go (`apps/api-go`); la demo corre sin Go |
| Editor de código | VS Code, Antigravity u otro | Escribir código |
| Una cuenta de GitHub con acceso al repositorio | — | Pull Requests |

Si ya usás **Laragon** (Windows), puede traer Git, Node y Python; igual verificá las versiones en el paso 3.

## 2. Instalar

**Windows** (PowerShell). Si no tenés `winget`, instalá cada programa desde su página oficial:

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
winget install GoLang.Go
```

Cerrá y volvé a abrir la terminal después de instalar.

**macOS:** `brew install git python@3.12 node go`

**Linux (Debian/Ubuntu):** `sudo apt install git python3.12 python3.12-venv` y Node.js 22 desde nodejs.org o con `nvm`; Go desde <https://go.dev/dl/>.

### Identidad de Git (importante)

Tus commits tienen que salir **a tu nombre**. Una sola vez:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"
```

Usá el mismo correo que tiene tu cuenta de GitHub.

## 3. Clonar y verificar

```bash
git clone https://github.com/tomascenturion895-prog/PLUVIFOR.git
cd PLUVIFOR
node scripts/verificar-entorno.mjs
```

El script no instala ni cambia nada: solo te dice qué **OK**, qué **FALTA** y qué **AVISO** (recomendado pero no obligatorio). Corregí lo que falte y volvé a correrlo hasta que diga «Todo listo para trabajar».

## 4. Variables de entorno

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

El archivo `.env` es solo tuyo y **no se sube nunca** (Git lo ignora). Ver `docs/seguridad-secretos.md`.

## 5. Backend

Desde `apps/backend`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
python -m app.cli reset-demo --yes # crea la base y carga los datos de demo (hace falta una vez)
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

**Cómo saber que funciona:** <http://localhost:8000/health> responde `{"status":"ok",...}` y <http://localhost:8000/api/stations> devuelve 3 estaciones. Si en cambio `/api/stations` da error 500, falta el paso `reset-demo`: la base está vacía y sin tablas.

En Windows puede que `python` no responda y haga falta `py -3.12 -m venv .venv`.

### Reiniciar la base de demo

Para dejar la demo en un estado conocido, sin internet, desde `apps/backend`:

```bash
python -m app.cli reset-demo          # pide confirmación
python -m app.cli reset-demo --yes    # sin preguntar (scripts)
```

Borra el archivo SQLite de `DATABASE_URL`, corre las migraciones y recarga las series del SIGA que están versionadas en `docs/datos/` (3 estaciones, 7.648 días), y recalcula las advertencias de racha de ceros. Se puede correr las veces que haga falta: siempre termina en el mismo estado.

Cuidados que ya tiene el comando:

- **Avisa antes de borrar** y dice qué archivo es. Sin una terminal para confirmar y sin `--yes`, no hace nada.
- **Solo toca un archivo SQLite local.** Con PostgreSQL o una base en memoria se niega sin borrar nada.
- **Revisa que estén los datos antes de borrar:** si falta un archivo de `docs/datos/`, no toca la base.

### Usar PostgreSQL en lugar de SQLite (opcional)

La demo corre con SQLite (un archivo, sin instalar nada). Para trabajar con PostgreSQL 16 el repositorio trae un `docker-compose.yml`. El controlador `psycopg` ya está en `requirements.txt`.

```bash
# 1. En tu .env, elegí una clave y poné la URL de PostgreSQL (la clave tiene que coincidir)
#    POSTGRES_PASSWORD=<una clave larga y al azar>
#    DATABASE_URL=postgresql+psycopg://pluvifor:<esa misma clave>@localhost:5432/pluvifor

# 2. Levantar la base (necesita Docker Desktop abierto)
docker compose up -d db
docker compose ps                    # esperá a que diga «healthy»

# 3. Migraciones y datos, igual que con SQLite (desde apps/backend, con el entorno virtual activo)
pip install -r requirements.txt
alembic upgrade head
python -m app.cli import-stations ../../docs/datos/estaciones_siga_formosa.csv
python -m app.cli import-rainfall --commit ../../docs/datos/lluvia_diaria_siga_formosa.csv
python -m app.cli recompute-flags
```

Para apagarla: `docker compose down` (los datos quedan) o `docker compose down -v` (los borra). La base solo escucha en `127.0.0.1`, no en la red.

**Correr las pruebas contra PostgreSQL:**

```bash
docker compose exec db createdb -U pluvifor pluvifor_test      # una sola vez
# Linux/macOS (Git Bash):
TEST_DATABASE_URL=postgresql+psycopg://pluvifor:<tu clave>@localhost:5432/pluvifor_test pytest
# Windows (PowerShell):
$env:TEST_DATABASE_URL="postgresql+psycopg://pluvifor:<tu clave>@localhost:5432/pluvifor_test"; pytest
```

Usá siempre una base **aparte** (`pluvifor_test`): las pruebas la vacían. El CI corre las migraciones y la suite contra PostgreSQL 16 en cada Pull Request.

**Qué se verificó (20/11/2026, PostgreSQL 16, Python 3.14):**

- Las 7 migraciones corren hasta la última (`alembic current` → `0007`).
- La importación real (3 estaciones y 7.648 días, 0 rechazos) da lo mismo que en SQLite.
- La suite completa del backend pasa con las pruebas que usan el fixture común apuntando a PostgreSQL. El resto de las pruebas (importación, migraciones, avisos y sensores) arma su propia base SQLite y sigue corriendo ahí.
- Un recorrido completo con los datos reales: lluvia, recurrencia, suscripción a avisos con los tres canales y sensores.

**Límites:** no hay PostGIS (las capas geográficas siguen siendo archivos GeoJSON), la API en Go todavía no lee de PostgreSQL (solo de SQLite; para PostgreSQL reenvía a Python), y no se probó concurrencia ni volumen.

## 6. API en Go

Desde `apps/api-go` (solo hace falta si vas a trabajar en esa parte; la demo no la necesita):

```bash
go vet ./... && go test ./...
go run ./cmd/api                    # http://localhost:8080/health   (puerto: API_GO_PORT)
```

**Cómo saber que funciona:** `/health` responde `{"status":"ok",...}`. Hoy la API en Go es un esqueleto: no sirve datos todavía, así que las pantallas siguen hablando con el backend en Python. Detalles en `apps/api-go/README.md`.

## 7. Frontend

Desde `apps/frontend`:

```bash
npm ci
npm test
npm run dev                         # http://localhost:5173
```

Se ejecutan los dos a la vez, cada uno en su terminal, y el backend tiene que estar corriendo (el frontend le pide los datos). **Cómo saber que funciona:** en <http://localhost:5173> se ve el Inicio con la leyenda de prototipo; en «Estación» aparecen 3 estaciones para elegir.

Pruebas de extremo a extremo en navegador real (escritorio, tableta y celular): `npm run test:e2e`. Detalles en `docs/qa/analisis-responsive.md`.

### Demo sin conexión a Internet

La demo funciona con el wifi apagado (SCRUM-92). Lo único que necesita es haber instalado todo antes (`pip install`, `npm ci`) y tener la base de demo: `python -m app.cli reset-demo --yes` (carga los datos versionados en SQLite, sin red).

- **Mapa:** por defecto el mapa base es **local**: se dibuja solo con los GeoJSON de `apps/frontend/public/geo` (provincia, departamentos y cursos de agua), sobre un fondo liso. No pide nada a Internet. Para sumar las calles de OpenStreetMap, con conexión, poné `VITE_MAPA_BASE=osm` en el `.env` y reiniciá `npm run dev`.
- **Interfaz:** no usa CDN, fuentes ni imágenes externas. Una prueba (`src/geo/sinInternet.test.ts`) falla si alguien agrega una dirección externa en `src` o en `index.html`.
- **Datos:** salen de SQLite local. El conector del SIGA en vivo, si no hay red, usa el CSV versionado y lo avisa.

Comprobado el 19/11/2026 en un navegador con todos los pedidos externos bloqueados: el mapa carga las capas del repositorio, 0 pedidos externos y 0 errores de JavaScript. Con `VITE_MAPA_BASE=osm` el mismo navegador intenta bajar 15 teselas, así que la diferencia se nota.

**Qué falla sin conexión (y es esperable):** con `VITE_MAPA_BASE=osm` el mapa queda sin calles; importar datos en vivo desde el SIGA o CHIRPS no se puede (el SIGA cae al CSV); instalar dependencias nuevas.

## 8. Revisión automática antes de cada commit (recomendado)

```bash
pip install pre-commit
pre-commit install
```

Frena el commit si hay una clave o un secreto. Ver `docs/seguridad-secretos.md`.

## 9. Tu herramienta de IA

Todas leen el mismo contexto del proyecto, que está en `AGENTS.md`.

| Persona | Herramienta | Qué hacer |
|---|---|---|
| Tomás, Santiago | Claude (Claude Code) | Abrir la carpeta del repositorio. `CLAUDE.md` importa `AGENTS.md` solo. |
| Alexia, Iván | Antigravity (Gemini Pro) y opencode | Abrir la carpeta del repositorio. Se puede apoyar en `AGENTS.md` y `GEMINI.md`. |
| Samuel | Antigravity (Gemini) | Igual que arriba. |

**Prueba de que leyó el contexto:** preguntale «¿qué reglas tiene este proyecto?». Tiene que mencionar que **un hueco de datos no es 0 mm** y que la **fecha de corte es el 31/10/2026**. Si no lo dice, pedile que lea `AGENTS.md`.

Las reglas de uso de IA (quién es responsable de lo que entra, no pegar secretos en chats) están en `docs/CONTRIBUTING.md`.

## 10. Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| PowerShell no deja activar el entorno virtual («la ejecución de scripts está deshabilitada») | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y reintentar |
| `python` o `pip` no se encuentra | Probar `py -3.12` (Windows) o `python3` (macOS/Linux); reinstalar marcando «Add to PATH» |
| `npm ci` falla por una versión vieja de Node | Actualizar a Node 22 o superior y repetir |
| El puerto 8000 o 5173 está ocupado | Cerrar el programa que lo usa, o arrancar con otro puerto (`--port 8001`) |
| Git muestra todos los archivos como modificados en Windows | Es un tema de finales de línea; el repositorio ya los normaliza (`.gitattributes`). Hacer `git pull` y reintentar |
| `git push` pide credenciales | Iniciar sesión en GitHub desde Git Credential Manager (Windows) o usar un token personal; **nunca** pegar el token en un chat |

## 11. Antes de abrir tu primer PR

1. Leer `docs/CONTRIBUTING.md` (ramas, commits, Pull Requests, Definition of Done).
2. Crear tu rama desde `main` actualizada: `feature/SCRUM-<n>-descripcion`.
3. Correr los tests y el lint de lo que tocaste.
