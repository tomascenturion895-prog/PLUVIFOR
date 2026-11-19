# apps

Código de la aplicación, dividido en tres partes que se ejecutan por separado.

| Carpeta | Qué contiene |
|---|---|
| `api-go/` | API en Go (esqueleto): `/health`, errores en español y contrato `openapi.yaml`. Todavía no sirve datos. |
| `backend/` | API en Python (FastAPI): reglas de calidad de datos, series, acumulados, comparador, importación y parte pluvial. |
| `frontend/` | Interfaz web en React + Vite: mapa provincial, estación, comparador, importación y parte pluvial. |

Cada carpeta tiene su propio README con los comandos para instalar, ejecutar y probar.
