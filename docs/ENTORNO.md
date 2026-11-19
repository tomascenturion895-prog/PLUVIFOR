# Entorno local

Cómo dejar tu computadora lista para trabajar en PLUVIFOR, desde cero. Sirve para las cinco personas del equipo y para cualquier herramienta de IA que uses.

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

## 1. Qué necesitás

| Herramienta | Versión | Para qué |
|---|---|---|
| Git | cualquiera reciente | Bajar y subir el código |
| Python | 3.12 o superior | Backend (API) |
| Node.js | 22 o superior (LTS) | Frontend, y el script de verificación |
| Editor de código | VS Code, Antigravity u otro | Escribir código |
| Una cuenta de GitHub con acceso al repositorio | — | Pull Requests |

Si ya usás **Laragon** (Windows), puede traer Git, Node y Python; igual verificá las versiones en el paso 3.

## 2. Instalar

**Windows** (PowerShell). Si no tenés `winget`, instalá cada programa desde su página oficial:

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

Cerrá y volvé a abrir la terminal después de instalar.

**macOS:** `brew install git python@3.12 node`

**Linux (Debian/Ubuntu):** `sudo apt install git python3.12 python3.12-venv` y Node.js 22 desde nodejs.org o con `nvm`.

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
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

En Windows puede que `python` no responda y haga falta `py -3.12 -m venv .venv`.

### Usar PostgreSQL en lugar de SQLite (opcional)

La demo corre con SQLite. Cambiar de motor es cambiar `DATABASE_URL`, y se comprobó el 19/11/2026 con PostgreSQL 16:

```bash
# 1. Una base vacía (ejemplo local)
createdb pluvifor
# 2. El controlador (no está en requirements.txt: ver «Diferencias»)
pip install "psycopg[binary]"
# 3. En .env
DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/pluvifor
# 4. Migraciones y datos, igual que con SQLite
alembic upgrade head
python -m app.cli import-stations ../../docs/datos/estaciones_siga_formosa.csv
python -m app.cli import-rainfall --commit ../../docs/datos/lluvia_diaria_siga_formosa.csv
python -m app.cli recompute-flags
```

**Qué se verificó:** las migraciones corren hasta la última; la importación real (3 estaciones y 7.648 días, 0 rechazos) da lo mismo que en SQLite; la estación 424 sale con acumulado 0,0 mm y la advertencia de racha de ceros, y la 425 con 1.265,0 mm; el parte pluvial responde 200; y 88 pruebas de la API (lluvia, estaciones, parte, calidad, modelos, salud y errores) pasan contra PostgreSQL.

**Diferencias y límites:**

- El controlador `psycopg` **no está en `requirements.txt`**: sumarlo es una dependencia nueva y no se agregó sin acordarlo. Hoy hay que instalarlo a mano.
- No se encontraron diferencias de comportamiento en lo probado. No hay tipos propios de un motor (enumeraciones como texto con restricciones).
- **No verificado:** la suite completa no corre contra PostgreSQL de forma automática (las pruebas de importación y de migraciones crean su propia base SQLite), no hay PostGIS y las capas geográficas siguen siendo archivos GeoJSON.
- Se probó con Python 3.13 y PostgreSQL 16 en una máquina de trabajo, sin concurrencia ni volumen.

## 6. Frontend

Desde `apps/frontend`:

```bash
npm ci
npm test
npm run dev                         # http://localhost:5173
```

Se ejecutan los dos a la vez, cada uno en su terminal.

## 7. Revisión automática antes de cada commit (recomendado)

```bash
pip install pre-commit
pre-commit install
```

Frena el commit si hay una clave o un secreto. Ver `docs/seguridad-secretos.md`.

## 8. Tu herramienta de IA

Todas leen el mismo contexto del proyecto, que está en `AGENTS.md`.

| Persona | Herramienta | Qué hacer |
|---|---|---|
| Tomás, Santiago | Claude (Claude Code) | Abrir la carpeta del repositorio. `CLAUDE.md` importa `AGENTS.md` solo. |
| Alexia, Iván | Antigravity (Gemini Pro) y opencode | Abrir la carpeta del repositorio. Se puede apoyar en `AGENTS.md` y `GEMINI.md`. |
| Samuel | Antigravity (Gemini) | Igual que arriba. |

**Prueba de que leyó el contexto:** preguntale «¿qué reglas tiene este proyecto?». Tiene que mencionar que **un hueco de datos no es 0 mm** y que la **fecha de corte es el 31/10/2026**. Si no lo dice, pedile que lea `AGENTS.md`.

Las reglas de uso de IA (quién es responsable de lo que entra, no pegar secretos en chats) están en `docs/CONTRIBUTING.md`.

## 9. Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| PowerShell no deja activar el entorno virtual («la ejecución de scripts está deshabilitada») | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y reintentar |
| `python` o `pip` no se encuentra | Probar `py -3.12` (Windows) o `python3` (macOS/Linux); reinstalar marcando «Add to PATH» |
| `npm ci` falla por una versión vieja de Node | Actualizar a Node 22 o superior y repetir |
| El puerto 8000 o 5173 está ocupado | Cerrar el programa que lo usa, o arrancar con otro puerto (`--port 8001`) |
| Git muestra todos los archivos como modificados en Windows | Es un tema de finales de línea; el repositorio ya los normaliza (`.gitattributes`). Hacer `git pull` y reintentar |
| `git push` pide credenciales | Iniciar sesión en GitHub desde Git Credential Manager (Windows) o usar un token personal; **nunca** pegar el token en un chat |

## 10. Antes de abrir tu primer PR

1. Leer `docs/CONTRIBUTING.md` (ramas, commits, Pull Requests, Definition of Done).
2. Crear tu rama desde `main` actualizada: `feature/SCRUM-<n>-descripcion`.
3. Correr los tests y el lint de lo que tocaste.
