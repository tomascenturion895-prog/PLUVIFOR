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
