# PLUVIFOR

**Pluviometría Integrada de Formosa**: reporte pluvial provincial con datos honestos.

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**
>
> Desarrollado por el Equipo 5 **SpaidyCode** (UTN, Extensión Áulica Formosa) para el Desafío 2 · Reporte pluvial de la *Operación Agua* (El Niño 2026/27).

---

## El problema

Con El Niño, la lluvia se comporta distinto según la zona de la provincia, y cada productor, ganadero o técnico necesita saber **cuánto llovió, dónde y desde cuándo**. Hoy ese dato está repartido entre redes de medición distintas (provincial, INTA, SMN, estimaciones satelitales), con horarios de corte diferentes, huecos de datos y estaciones que dejan de reportar sin avisar.

## Qué es PLUVIFOR

Un sistema web que reúne las series de lluvia de toda la provincia y permite **consultarlas por estación, zona y período**, sin ocultar la calidad del dato. La idea central: **un hueco no es un cero**. Si una estación no informó, el sistema lo muestra como "sin dato", y si hay señales de que algo anda mal, lo advierte.

## Qué hace (estado real al 19/11/2026)

| Módulo | Qué existe hoy |
|---|---|
| **Ingesta y auditoría** | Importación de lluvia diaria y catálogo de estaciones por CSV con auditoría previa (qué se acepta y qué se rechaza) y confirmación con clave de administración. Historial de cargas. Registro de limpieza en `docs/entrega/registro-de-limpieza.md`. |
| **Mapa provincial** | Mapa con los departamentos y los acumulados por período, con trazo discontinuo donde no hay dato. |
| **Estación** | Ficha con acumulado, cobertura, días «sin dato» / «fila sin valor», advertencias de calidad y gráfico diario. |
| **Parte pluvial** | Resumen de hasta 20 estaciones con fuente, categoría, fecha de corte y advertencias. |
| **Comparador** | La API compara estaciones y devuelve las advertencias de comparabilidad (`/api/rainfall/compare`). **La pantalla todavía dice «en construcción».** |
| **Salud de la red** y **Ayuda** | Pantallas **en construcción**. |

## Principios de rigor

- **Hueco ≠ 0 mm.** Nunca se reemplaza un dato faltante por cero.
- **Observado, referencia y estimado se muestran por separado.** Una estimación satelital no se mezcla con una medición en estación.
- **Seis advertencias de comparabilidad:** horarios de corte distintos entre redes, observado vs. estimado, cobertura despareja, dato sin validar, rachas prolongadas de cero (60 días o más) e inconsistencia con estaciones vecinas.
- **Todo dato lleva su fuente, su fecha de corte y su categoría.** Fecha de corte de los datos del prototipo: 31/10/2026.

## Fuentes de datos

- **Datos reales de la demo:** series diarias de 3 estaciones del SIGA/INTA (7.648 días en `docs/datos/`) y, aparte, la normal mensual 1991-2020 de Formosa Aero del SMN como referencia climática (CC BY 2.5 AR), que se carga con `python -m app.cli import-normals` (no la trae `reset-demo`).
- **Conector preparado, sin datos cargados:** CHIRPS v3 como lluvia estimada, siempre separada de lo medido.
- **Sin verificar:** red provincial, UPCA, SNIH y la API del INA (licencia y series sin confirmar). No se cargó nada de ellas.

El detalle de cada una (licencia, horario de corte, pendientes) está en `docs/fuentes/README.md`.

## Alcance

**Incluye:** consulta y comparación de lluvia, calidad del dato, mapa provincial, parte pluvial.

**Requiere fundamento** (puede sumarse si se justifica cómo ayuda a la solución; ver `AGENTS.md`): alturas de ríos y riachos, predicción de afectaciones, zonas de riesgo, evacuaciones, identificación de atajaderos.

## Cómo correrlo

Hace falta Git, Python 3.12 o superior y Node.js 22 o superior (y Go 1.24 o superior solo si vas a trabajar en la API en Go). La guía completa, con Windows y macOS, está en `docs/ENTORNO.md`. En resumen, desde la raíz del repositorio y con dos terminales:

```bash
cp .env.example .env                       # Windows: copy .env.example .env

# Terminal 1 · API (http://localhost:8000/health)
cd apps/backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m app.cli reset-demo --yes         # crea la base y carga los datos de demo (sin internet)
uvicorn app.main:app --reload

# Opcional · API en Go (http://localhost:8080/health): hoy es un esqueleto, sin datos
cd apps/api-go && go run ./cmd/api

# Terminal 2 · Interfaz (http://localhost:5173)
cd apps/frontend
npm ci
npm run dev
```

**Variables de entorno** (solo nombres; los valores van en `.env`, que Git ignora): `DATABASE_URL` (SQLite por defecto), `DATA_CUTOFF_DATE` (2026-10-31), `CORS_ORIGINS`, `ADMIN_API_KEY` (sin ella, importar y confirmar cargas queda deshabilitado), `MAX_REQUEST_BYTES`, `MAX_UPLOAD_BYTES`, `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_IMPORT_PER_MINUTE` y `VITE_API_URL`. Ver `.env.example` y `docs/seguridad-secretos.md`.

## Pruebas

```bash
cd apps/api-go   && go vet ./... && go test ./...
cd apps/backend  && pytest && ruff check . && ruff format --check .
cd apps/frontend && npm test && npm run lint && npm run format:check && npm run build
```

Al 19/11/2026: 331 pruebas de backend y 119 de frontend en verde. Los planes y resultados de QA están en `docs/qa/`.

## Tecnología

- **API:** Go (`apps/api-go`, solo biblioteca estándar), por rapidez. Hoy es un esqueleto: `/health`, errores y contrato `openapi.yaml`.
- **Procesamiento y API de datos:** Python, FastAPI, Pydantic, SQLAlchemy y Alembic sobre SQLite (PostgreSQL por `DATABASE_URL`: ver `docs/ENTORNO.md`). Es quien hoy responde todas las rutas `/api/*`, y donde irán el procesamiento y la predicción con IA.
- **Frontend:** React 19, TypeScript, Vite, Recharts y Leaflet.
- **Capas geográficas:** GeoJSON de departamentos y cursos de agua (IGN), incluidas en el repositorio.
- **Diseño por conectores:** cada fuente de datos se agrega sin tocar el resto del sistema.

## Estructura del repositorio

```
pluvifor/
├── apps/
│   ├── api-go/     # API en Go (esqueleto)
│   ├── backend/    # Procesamiento, reglas de calidad, importación y API de datos
│   └── frontend/   # Interfaz web
├── docs/           # Ficha técnica, fuentes, datos, QA, entrega
├── scripts/        # Verificación del entorno
├── AGENTS.md       # Reglas del proyecto para asistentes de IA
└── .env.example
```

## Límites conocidos

Es un prototipo. Lo que **no** hay, dicho de frente:

- No hay despliegue en línea: corre en la computadora local.
- La API en Go es un esqueleto (`/health` y errores): todavía no tiene driver de base de datos ni sirve estaciones o lluvia. Esas rutas responden desde Python.
- No hay predicción con IA todavía: es parte del plan para la parte de Python.
- Hay series reales de solo 3 estaciones del SIGA/INTA. La lista de las 34 estaciones provinciales no está disponible.
- Las pantallas Comparador, Salud de la red y Ayuda están en construcción.
- No se probó en celulares reales; el análisis responsive es simulado.
- Los datos tienen fecha de corte 31/10/2026 y no se actualizan solos.

## Equipo

**SpaidyCode · Equipo 5** — UTN, Extensión Áulica Formosa.

## Licencia y datos

Los datos pertenecen a sus respectivas fuentes y se citan en `docs/`. Este prototipo no es una herramienta oficial ni reemplaza los reportes de los organismos competentes.
