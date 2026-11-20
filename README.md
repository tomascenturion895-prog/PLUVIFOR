# PLUVIFOR

**Pluviometría Integrada de Formosa**: reporte pluvial provincial con datos honestos.

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**
>
> Desarrollado por el Equipo 5 **SpaidyCode** (UTN, Extensión Áulica Formosa) para el Desafío 2 · Reporte pluvial de la *Operación Agua* (El Niño 2026/27).

---

## Índice

1. [El problema](#el-problema)
2. [Qué es PLUVIFOR](#qué-es-pluvifor)
3. [Qué hace hoy](#qué-hace-hoy)
4. [Principios de rigor](#principios-de-rigor)
5. [**Instalación paso a paso**](#instalación-paso-a-paso)
6. [Pruebas](#pruebas)
7. [Tecnología y estructura](#tecnología-y-estructura)
8. [Documentación](#documentación)
9. [Límites conocidos](#límites-conocidos)

---

## El problema

Con El Niño, la lluvia se comporta distinto según la zona de la provincia, y cada productor, ganadero o técnico necesita saber **cuánto llovió, dónde y desde cuándo**. Hoy ese dato está repartido entre redes de medición distintas (provincial, INTA, SMN, estimaciones satelitales), con horarios de corte diferentes, huecos de datos y estaciones que dejan de reportar sin avisar.

## Qué es PLUVIFOR

Un sistema web que reúne las series de lluvia de toda la provincia y permite **consultarlas por estación, zona y período**, sin ocultar la calidad del dato. La idea central: **un hueco no es un cero**. Si una estación no informó, el sistema lo muestra como «sin dato», y si hay señales de que algo anda mal, lo advierte.

## Qué hace hoy

| Módulo | Qué existe |
|---|---|
| **Ingesta y auditoría** | Importación de lluvia diaria y catálogo de estaciones por CSV, con auditoría previa (qué se acepta y qué se rechaza) y confirmación. Historial de cargas con quién hizo cada una. |
| **Mapa, estación y parte** | Mapa provincial con acumulados; ficha por estación con gráfico diario, cobertura, advertencias de calidad, eventos intensos (≥50 y ≥100 mm), rachas secas y recurrencia histórica; parte pluvial de hasta 20 estaciones. |
| **Comparador y salud de la red** | Comparación de estaciones con las seis advertencias de comparabilidad; qué estaciones siguen reportando y cuáles dejaron de hacerlo. |
| **Vista 3D y maqueta** | Exposición pluvial por departamento (rotulada como estimado) sobre el mapa real de la provincia. |
| **Sensores (simulados)** | Contrato de ingesta, simulador y pantalla por dispositivo con su estado. Todo entra rotulado como simulado y nunca se mezcla con lo observado. |
| **Avisos a la población (canales simulados)** | Suscripción con código, correo opcional, varias estaciones y baja. Los avisos salen por WhatsApp, correo y notificación del sistema, **todos simulados**: no se envía nada real. |
| **Cuentas** | Registro e inicio de sesión con roles (ciudadano, operador, administrador) y registro de quién cargó cada dato. |
| **Interfaz** | Español, inglés, guaraní, wichí y toba; temas claro, oscuro y para daltonismo; panel de accesibilidad; funciona sin internet. |

El detalle de cada módulo, con lo que **no** hace, está en `docs/`.

## Principios de rigor

- **Hueco ≠ 0 mm.** Nunca se reemplaza un dato faltante por cero.
- **Observado, referencia y estimado se muestran por separado.** Una estimación satelital o una lectura simulada no se mezcla con una medición en estación.
- **Seis advertencias de comparabilidad:** horarios de corte distintos entre redes, observado vs. estimado, cobertura despareja, dato sin validar, rachas prolongadas de cero (60 días o más) e inconsistencia con estaciones vecinas.
- **Todo dato lleva su fuente, su fecha de corte y su categoría.** Fecha de corte de los datos del prototipo: **31/10/2026**.
- **Los avisos nunca ordenan evacuar.** Son informativos y remiten a Defensa Civil.

Datos reales de la demo: series diarias de 3 estaciones del SIGA/INTA (7.648 días en `docs/datos/`) y la normal mensual 1991-2020 de Formosa Aero del SMN como referencia. El detalle de cada fuente (licencia, horario de corte, pendientes) está en `docs/fuentes/README.md`.

---

# Instalación paso a paso

Esta guía lleva a alguien que **nunca abrió el proyecto** desde cero hasta tenerlo funcionando en su computadora. Cada paso dice qué escribir y qué tendrías que ver. Si algo no sale como dice, andá a [Problemas frecuentes](#problemas-frecuentes).

**Al terminar vas a tener:** la API corriendo en <http://localhost:8000>, la interfaz en <http://localhost:5173>, una base de datos con los datos reales de la demo y una cuenta de administrador.

> **Dónde se escribe cada comando.** Todo se escribe en una terminal: en Windows, **PowerShell** (botón de Inicio, escribí «PowerShell»); en macOS, **Terminal**; en Linux, la terminal de siempre. Donde el comando es distinto según el sistema, lo indica. Las líneas que empiezan con `#` son comentarios: no hace falta escribirlas.

## Paso 1 · Instalar los programas

Hacen falta **cuatro programas** (el quinto es opcional):

| Programa | Versión | Para qué | ¿Obligatorio? |
|---|---|---|---|
| Git | cualquiera reciente | Bajar el código | Sí |
| Python | **3.12 o superior** | La API y el procesamiento de datos | Sí |
| Node.js | **22 o superior** | La interfaz web | Sí |
| Go | 1.24 o superior | Una API más rápida para las consultas | No (la demo corre sin Go) |
| Docker Desktop | reciente | Una base PostgreSQL local | No (la demo usa SQLite, un archivo) |

**Windows** (PowerShell). Si `winget` no existe en tu computadora, instalá cada programa desde su página oficial (git-scm.com, python.org, nodejs.org):

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

**macOS** (con [Homebrew](https://brew.sh)):

```bash
brew install git python@3.12 node
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip
# Node.js 22 o superior: https://nodejs.org (o con nvm)
```

**Cerrá la terminal y abrí una nueva** (así reconoce lo recién instalado). Después comprobá las versiones:

```bash
git --version        # cualquiera
python --version     # tiene que decir 3.12 o más.  En macOS/Linux probá:  python3 --version
node --version       # tiene que decir v22 o más
```

> En Windows, si `python` abre la tienda de Microsoft o no se encuentra, probá `py -3.12 --version`. Si funciona, usá `py -3.12` en lugar de `python` en el paso 5.

**Identidad de Git (una sola vez).** Tus cambios tienen que salir a tu nombre:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"
```

## Paso 2 · Bajar el código

```bash
git clone https://github.com/tomascenturion895-prog/PLUVIFOR.git
cd PLUVIFOR
```

Tendrías que ver las carpetas `apps`, `docs` y `scripts`. **Todos los comandos siguientes se escriben desde esta carpeta (`PLUVIFOR`)** salvo que diga lo contrario.

## Paso 3 · Verificar que tu computadora está lista

```bash
node scripts/verificar-entorno.mjs
```

El script **no instala ni cambia nada**: solo muestra `OK`, `FALTA` o `AVISO` por cada requisito. Corregí lo que diga `FALTA` y volvé a correrlo hasta ver «Todo listo para trabajar».

## Paso 4 · Crear tu archivo de configuración (`.env`)

El `.env` guarda tus claves y opciones. **Nunca se sube a Git** (está ignorado a propósito).

```bash
# macOS / Linux / Git Bash:
cp .env.example .env
# Windows (PowerShell):
copy .env.example .env
```

Ahora necesitás inventar **cuatro claves**. Cada una tiene que ser un texto largo y al azar, y **distinta de las otras**. Para generar una, corré esto (en el paso 5 tendrás Python con su entorno; por ahora sirve el Python del sistema):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# macOS/Linux: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiá el resultado. Repetilo cuatro veces. Abrí el archivo `.env` con cualquier editor (el Bloc de notas sirve) y completá estas líneas:

```ini
ADMIN_API_KEY=<primera clave>      # protege importar datos y cargar reportes
DEVICE_API_KEY=<segunda clave>     # protege la ingesta de sensores simulados
ALERTS_SECRET=<tercera clave>      # resume teléfonos y códigos de los avisos
ALERTS_DEMO=true                   # solo para presentaciones: muestra el celular y el correo simulados
```

> Anotá la `ADMIN_API_KEY`: la vas a escribir en algunas pantallas del personal. Lo demás del `.env` puede quedar como está. Si dejás una clave vacía, esa función queda **cerrada** (es a propósito: sin clave no se puede escribir).
>
> Con `ALERTS_DEMO=true` cualquiera que conozca un teléfono puede ver sus mensajes simulados. Es solo para presentaciones; con canales reales debe estar en `false`.

## Paso 5 · Instalar y preparar el backend (la API de datos)

Desde la carpeta `PLUVIFOR`:

```bash
cd apps/backend
```

**5.1 · Crear el entorno virtual de Python** (una carpeta `.venv` con las librerías del proyecto, aislada del resto de tu computadora):

```bash
python -m venv .venv
```

**5.2 · Activarlo.** Cambia según tu terminal:

| Terminal | Comando |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows `cmd` | `.venv\Scripts\activate.bat` |
| Git Bash (Windows) | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

Tendrías que ver `(.venv)` al principio de la línea de la terminal. **Cada vez que abras una terminal nueva para trabajar en el backend, tenés que activarlo de nuevo.**

> Si PowerShell dice «la ejecución de scripts está deshabilitada», corré una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí el comando.

**5.3 · Instalar las librerías:**

```bash
pip install -r requirements-dev.txt
```

Tarda uno o dos minutos. Termina con «Successfully installed …».

**5.4 · Crear la base de datos y cargar los datos reales de la demo:**

```bash
python -m app.cli reset-demo --yes
```

Esto crea el archivo `pluvifor.db` (SQLite), aplica todas las migraciones y carga **3 estaciones y 7.648 días de lluvia**. Tendrías que ver algo como:

```
Base reiniciada: ...pluvifor.db
Estaciones: 3 · días de lluvia: 7648 · rechazados: 0 · tramos de ceros prolongados: 1
```

> Es seguro repetirlo: **borra y recrea** esa base (por eso pide `--yes`). Solo toca un archivo SQLite local.

**5.5 · Cargar la normal climática del SMN** (la referencia que se muestra aparte de lo observado):

```bash
python -m app.cli import-normals
```

**5.6 · Crear tu cuenta de administrador.** Pide una contraseña de **10 caracteres o más** (no se ve mientras la escribís) y que la repitas:

```bash
python -m app.cli create-user --email tu@correo.com --role administrador
```

Tendrías que ver `Cuenta creada: tu@correo.com · rol administrador`. Con esa cuenta vas a poder ingresar en la interfaz y asignarle roles a otras personas.

## Paso 6 · Levantar el backend

Con el entorno virtual activo (`(.venv)` visible) y dentro de `apps/backend`:

```bash
uvicorn app.main:app --reload
```

Dejá **esta terminal abierta**: es el servidor. Para comprobar que anda, abrí en el navegador:

- <http://localhost:8000/health> → tiene que mostrar `{"status":"ok", ...}`.
- <http://localhost:8000/docs> → la documentación interactiva de la API.
- <http://localhost:8000/api/stations> → las estaciones, en JSON: las 3 del SIGA/INTA (51, 424 y 425) y la de referencia del SMN (87162) que cargaste en el paso 5.5.

## Paso 7 · Instalar y levantar la interfaz

Abrí una **segunda terminal** (la del backend sigue corriendo), andá a la carpeta `PLUVIFOR` y escribí:

```bash
cd apps/frontend
npm ci
npm run dev
```

`npm ci` instala las librerías (puede tardar un par de minutos la primera vez). Cuando `npm run dev` termine de arrancar, abrí <http://localhost:5173>. Dejá también **esta terminal abierta**.

> La interfaz le pide los datos al backend en el puerto 8000. **Los dos tienen que estar corriendo a la vez.** Para apuntarla a otro lado, definí `VITE_API_URL` (ver `.env.example`).

## Paso 8 · Comprobar que todo funciona

Recorré esta lista en <http://localhost:5173>. Si todo coincide, la instalación está bien:

| Qué hacer | Qué tendrías que ver |
|---|---|
| Abrir **Inicio** | La pantalla de bienvenida y, abajo, la leyenda «PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial». |
| **Estación** → elegir la **424** (El Colorado) | Un gráfico diario con franjas rayadas (días **sin dato**) y una **advertencia de racha de ceros** de 281 días: el sistema no da por buena una racha tan larga. |
| **Estación** → elegir la **425**, del 1/1/2016 al 31/12/2016 | Un acumulado de **1.528 mm**. La 424, en el mismo período, no puede decir lo mismo: es el caso que muestra por qué un cero prolongado se advierte. |
| **Mapa** | Los departamentos de Formosa con las estaciones que tienen coordenadas. |
| **Cuenta** → «Ya tengo cuenta» | Ingresá con el correo y la contraseña del paso 5.6. Tendrías que ver tu rol «Administrador» y el panel de cuentas. |
| **Avisos** | Registrá un teléfono (por ejemplo `+54 370 4123456`) y un correo: aparece un **celular con un chat de WhatsApp** con el código. Escribilo, confirmá, y abrí «Panel del personal» → «Usar el día de ejemplo» → «Enviar aviso (simulado)»: el aviso **llega al celular, al correo y a la campana**. |

El guion completo de la demostración de avisos está en `docs/entrega/demo-avisos.md`.

---

## Opcionales

### Usar PostgreSQL en lugar de SQLite

La demo corre con SQLite (un archivo, sin instalar nada). Para trabajar con una base de verdad:

1. Abrí **Docker Desktop** y esperá a que diga que está corriendo.
2. En tu `.env`, completá la clave de la base y la URL (la clave tiene que ser **la misma** en las dos líneas):

   ```ini
   POSTGRES_PASSWORD=<una clave larga y al azar>
   DATABASE_URL=postgresql+psycopg://pluvifor:<esa misma clave>@127.0.0.1:5432/pluvifor
   ```

   > **Escribí `127.0.0.1` y no `localhost`.** En Windows, `localhost` puede intentar primero la dirección IPv6 y esperar unos 8 segundos **en cada conexión**: la carga de datos parece colgada. Si el puerto 5432 ya lo usa otro PostgreSQL instalado en tu computadora, agregá por ejemplo `POSTGRES_PORT=5433` al `.env` y poné ese mismo número en la URL.

3. Desde `PLUVIFOR`, levantá la base y esperá a que diga `healthy`:

   ```bash
   docker compose up -d db
   docker compose ps
   ```

4. Desde `apps/backend` (con el entorno virtual activo), creá las tablas y cargá los datos:

   ```bash
   alembic upgrade head
   python -m app.cli import-stations ../../docs/datos/estaciones_siga_formosa.csv
   python -m app.cli import-rainfall --commit ../../docs/datos/lluvia_diaria_siga_formosa.csv
   python -m app.cli import-normals
   python -m app.cli recompute-flags
   python -m app.cli create-user --email tu@correo.com --role administrador
   ```

Para apagarla: `docker compose down` (los datos quedan) o `docker compose down -v` (los **borra**). `reset-demo` no funciona con PostgreSQL a propósito: se niega a borrar algo que no sea un archivo SQLite local. Más detalles en `docs/ENTORNO.md`.

### Cargar sensores simulados

Con el backend corriendo y `DEVICE_API_KEY` en el `.env`, en otra terminal (en `apps/backend`, con el entorno virtual activo):

```bash
python -m simulador --url http://localhost:8000 --dispositivos 3 --dias 7
```

Después abrí **Sensores** en la interfaz. Todo lo que aparece está rotulado como **simulado**. Ver `docs/ingesta-sensores.md`.

### La API en Go

Go atiende las consultas de estaciones y lluvia más rápido y reenvía el resto al backend en Python. Hace falta Go 1.24+ (<https://go.dev/dl/>). Con el backend corriendo, en otra terminal desde `apps/api-go`:

```bash
go run -tags sqlite ./cmd/api        # http://localhost:8080/health
```

Y para que la interfaz le hable a Go (desde `apps/frontend`):

```bash
# macOS / Linux / Git Bash:
VITE_API_URL=http://localhost:8080 npm run dev
# Windows (PowerShell):
$env:VITE_API_URL="http://localhost:8080"; npm run dev
```

La primera vez descarga el driver de SQLite. Ver `apps/api-go/README.md`.

---

## Problemas frecuentes

| Qué pasa | Qué hacer |
|---|---|
| `python` no se encuentra, o abre la tienda de Microsoft | En Windows probá `py -3.12`. Si no, reinstalá Python marcando «Add python.exe to PATH» y abrí una terminal nueva |
| `pip install` falla con «no matching distribution» | Tu Python es más viejo que 3.12: `python --version` y actualizalo |
| PowerShell: «la ejecución de scripts está deshabilitada» | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí la activación del entorno |
| No veo `(.venv)` en la terminal | No está activado: repetí el paso 5.2 en **esa** terminal |
| `npm ci` falla por la versión de Node | Instalá Node 22 o superior y repetí |
| La interfaz carga pero dice «No se pudo conectar con el servidor» | El backend no está corriendo: levantalo (paso 6) y recargá |
| Los gráficos están vacíos | No cargaste los datos: repetí el paso 5.4 |
| «El puerto 8000 (o 5173) está ocupado» | Cerrá lo que lo usa, o arrancá en otro puerto: `uvicorn app.main:app --reload --port 8001` (y definí `VITE_API_URL=http://localhost:8001`) |
| La pantalla Avisos dice «la vista de demostración está apagada» | Falta `ALERTS_DEMO=true` en el `.env`; reiniciá el backend |
| «Los avisos están deshabilitados» | Falta `ALERTS_SECRET` en el `.env`; reiniciá el backend |
| Importar o cargar un reporte dice «La escritura está deshabilitada» | Falta `ADMIN_API_KEY` en el `.env` (o ingresá con una cuenta de operador o administrador) |
| Error de tabla o columna que no existe | La base está desactualizada: `alembic upgrade head` (o `python -m app.cli reset-demo --yes` con SQLite) |
| `create-user` dice «Sin una terminal» | Corrélo en una terminal normal, o definí la variable `PLUVIFOR_NEW_USER_PASSWORD` solo para ese comando |
| `docker compose up` dice que falta `POSTGRES_PASSWORD` | Completalo en el `.env` (paso de PostgreSQL) |
| `docker compose up` dice «ports are not available» (puerto 5432) | Ya hay otro PostgreSQL en tu computadora usando ese puerto. Poné otro en el `.env` (`POSTGRES_PORT=5433`) y el mismo número en `DATABASE_URL`, y repetí `docker compose up -d db` |
| Con PostgreSQL todo tarda muchísimo (cada comando se queda esperando) | En `DATABASE_URL` escribí `127.0.0.1` en lugar de `localhost` |
| PostgreSQL dice «la autentificación password falló» | La clave de `DATABASE_URL` no coincide con `POSTGRES_PASSWORD`, o estás apuntando a otro PostgreSQL que ya tenías (revisá el puerto). Si cambiaste la clave después de crear la base, `docker compose down -v` y volvé a empezar (borra los datos) |
| Git muestra todos los archivos como modificados en Windows | Es un tema de finales de línea; el repositorio ya los normaliza. Hacé `git pull` y reintentá |

Más casos en `docs/ENTORNO.md`.

---

## Pruebas

Antes de abrir un Pull Request, corré las del área que tocaste. Cada una en su carpeta, con el entorno virtual activo para el backend:

```bash
cd apps/backend  && pytest && ruff check . && ruff format --check .
cd apps/frontend && npm test && npm run lint && npm run format:check && npm run build
cd apps/api-go   && go vet ./... && go test ./... && gofmt -l .      # gofmt no debe listar nada
```

Las pruebas del backend usan su propia base temporal: **no tocan** tu `pluvifor.db`. Los planes y resultados de QA están en `docs/qa/`. Las reglas de ramas, commits y Pull Requests están en `docs/CONTRIBUTING.md`.

## Tecnología y estructura

| Parte | Tecnología |
|---|---|
| **Procesamiento y API de datos** | Python, FastAPI, Pydantic, SQLAlchemy, Alembic. SQLite por defecto; PostgreSQL con `DATABASE_URL` |
| **API de consultas** | Go (`apps/api-go`), solo biblioteca estándar más el driver de SQLite. Atiende estaciones y lluvia y reenvía el resto a Python |
| **Interfaz** | React 19, TypeScript, Vite, Recharts, Leaflet y three.js |
| **Capas geográficas** | GeoJSON de departamentos y cursos de agua (IGN), dentro del repositorio |
| **CI** | GitHub Actions: Go, Python (SQLite y PostgreSQL), interfaz y escaneo de secretos |

```
PLUVIFOR/
├── apps/
│   ├── api-go/      # API en Go (consultas y contrato openapi.yaml)
│   ├── backend/     # Procesamiento, reglas de calidad, importación, avisos, cuentas y API de datos
│   └── frontend/    # Interfaz web
├── docs/            # Ficha técnica, fuentes, datos, decisiones, QA y entrega
├── scripts/         # Verificación del entorno
├── docker-compose.yml   # PostgreSQL local (opcional)
├── .env.example     # Variables de entorno de ejemplo, sin secretos
└── AGENTS.md        # Reglas del proyecto para asistentes de IA
```

## Documentación

| Tema | Dónde |
|---|---|
| Entorno local y problemas | `docs/ENTORNO.md` |
| Cómo trabajamos (ramas, commits, PR) | `docs/CONTRIBUTING.md` |
| Modelo de datos y relaciones | `docs/modelo-datos.md` |
| Cuentas y roles | `docs/cuentas.md` |
| Avisos a la población y su demostración | `docs/ingesta-avisos.md`, `docs/entrega/demo-avisos.md` |
| Sensores simulados | `docs/ingesta-sensores.md` |
| Fuentes de datos y licencias | `docs/fuentes/README.md` |
| Decisiones y fundamento de cada tema | `docs/decisiones/` |
| Ficha técnica y arquitectura objetivo | `docs/entrega/` |
| Contrato de la API | `apps/api-go/openapi.yaml` |

## Límites conocidos

Es un prototipo. Lo que **no** hay, dicho de frente:

- **No se envía ningún mensaje real.** WhatsApp, correo y notificaciones son canales simulados; conectar uno real necesita una cuenta de empresa verificada, un número, plantillas aprobadas y un dominio de correo.
- **No hay predicción de lluvia, zonas inundables ni evacuaciones.** Faltan datos oficiales y relieve, y no se inventan. Lo que existe es la frecuencia histórica de eventos intensos, que describe el pasado y no pronostica.
- No hay despliegue en línea: corre en la computadora local.
- Hay series reales de solo 3 estaciones del SIGA/INTA. La lista de las 34 estaciones provinciales no está disponible.
- Las cuentas no tienen recuperación de contraseña ni segundo factor.
- No se probó en celulares reales; el análisis responsive es simulado.
- Los datos tienen fecha de corte 31/10/2026 y no se actualizan solos.

## Equipo

**SpaidyCode · Equipo 5** — UTN, Extensión Áulica Formosa.

## Licencia y datos

Los datos pertenecen a sus respectivas fuentes y se citan en `docs/`. Este prototipo no es una herramienta oficial ni reemplaza los reportes de los organismos competentes.
