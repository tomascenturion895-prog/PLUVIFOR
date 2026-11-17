# Backend · API de PLUVIFOR

API en Python (FastAPI) del reporte pluvial de Formosa.

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

## Requisitos

- Python 3.12

## Instalar y ejecutar

Desde `apps/backend`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp ../../.env.example ../../.env   # Windows: copy ..\..\.env.example ..\..\.env
uvicorn app.main:app --reload
```

- API: <http://localhost:8000/health>
- Documentación interactiva: <http://localhost:8000/docs> (apagada cuando `APP_ENV=production`)

## Probar

```bash
pytest
ruff check .
ruff format --check .
```

## Estructura

```
app/
  main.py        Crea la aplicación (create_app) y registra rutas, CORS y errores
  config.py      Variables de entorno (ver .env.example)
  errors.py      Formato único de error
  api/           Rutas (una por recurso)
  services/      Lógica de negocio, sin dependencias de FastAPI
  schemas/       Modelos de entrada y salida (Pydantic)
tests/           Pruebas
```

## Formato de error

Todos los errores tienen la misma forma y nunca incluyen detalles internos ni el valor que envió el usuario:

```json
{ "error": { "code": "validation_error", "message": "Los datos enviados no son válidos.", "details": [{ "field": "query.from", "message": "..." }] } }
```

## Reglas del proyecto

Un hueco de datos no es 0 mm. Ver `AGENTS.md` y `docs/CONTRIBUTING.md`.

## Base de datos

```
alembic upgrade head      # crea/actualiza las tablas (usa DATABASE_URL)
alembic revision --autogenerate -m "descripcion"   # tras cambiar un modelo
```

Las reglas de calidad (un hueco no es 0 mm, categorías, unidad) son restricciones de la base; ver `docs/modelo-datos.md`.

## Importar series

```
python -m app.cli import-stations ../../docs/datos/estaciones_siga_formosa.csv
python -m app.cli import-rainfall ../../docs/datos/lluvia_diaria_siga_formosa.csv           # audita: no guarda
python -m app.cli import-rainfall --commit ../../docs/datos/lluvia_diaria_siga_formosa.csv  # guarda
```

Cada corrida deja una fila en `import_logs` (huella sha256, filas leídas/aceptadas/rechazadas y motivos). Volver a cargar el mismo archivo no duplica filas. Se rechazan fechas posteriores al corte (31/10/2026), valores negativos, estaciones inexistentes y estados incoherentes.

## Banderas de calidad

```
python -m app.cli recompute-flags   # recalcula rachas de ceros (60 días o más)
```

Un hueco (`sin_fila`, `fila_sin_valor`) corta la racha: no se afirma que no llovió un día sin dato. Las banderas se reemplazan en cada corrida y guardan la versión de la regla.
