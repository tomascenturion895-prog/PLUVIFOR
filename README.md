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

## Qué hace

| Módulo | Función |
|---|---|
| **1. Ingesta y auditoría** | Carga datos de distintas fuentes, los normaliza y deja un registro de limpieza de cada decisión tomada. |
| **2. Mapa provincial** | Muestra las estaciones de todo el territorio, no solo la capital, con acumulados por período. |
| **3. Comparador** | Compara estaciones, zonas y períodos, con unidades claras y separación entre lluvia observada y estimada. |
| **4. Parte pluvial** | Genera un resumen listo para compartir, con las advertencias de calidad incluidas. |

## Principios de rigor

- **Hueco ≠ 0 mm.** Nunca se reemplaza un dato faltante por cero.
- **Observado, referencia y estimado se muestran por separado.** Una estimación satelital no se mezcla con una medición en estación.
- **Seis advertencias de comparabilidad:** horarios de corte distintos entre redes, observado vs. estimado, cobertura despareja, dato sin validar, rachas prolongadas de cero (60 días o más) e inconsistencia con estaciones vecinas.
- **Todo dato lleva su fuente, su fecha de corte y su categoría.** Fecha de corte de los datos del prototipo: 31/10/2026.

## Fuentes de datos

- Series diarias de estaciones INTA (SIGA).
- Datos provistos en el kit del AI LAB.
- CHIRPS v3 como referencia estimada (CC BY 4.0), siempre separada de los datos medidos.
- Otras fuentes en evaluación (por ejemplo, la API del INA), sujetas a verificación.

El detalle y el tratamiento de cada una están en `docs/` (ficha de fuentes en `docs/fuentes/README.md` y registro de limpieza).

## Alcance

**Incluye:** consulta y comparación de lluvia, calidad del dato, mapa provincial, parte pluvial.

**Requiere fundamento** (puede sumarse si se justifica cómo ayuda a la solución; ver `AGENTS.md`): alturas de ríos y riachos, predicción de afectaciones, zonas de riesgo, evacuaciones, identificación de atajaderos.

## Tecnología

- **Backend:** FastAPI, Pydantic, SQLAlchemy, SQLite (con opción de migrar a PostgreSQL/PostGIS).
- **Frontend:** React, Vite, Recharts, Leaflet.
- **Capas geográficas:** GeoJSON de departamentos y cursos de agua (IGN), incluidas en el repositorio.
- **Diseño por conectores:** cada fuente de datos se agrega sin tocar el resto del sistema.

## Estructura del repositorio

```
pluvifor/
├── apps/
│   ├── backend/    # API y reglas de calidad
│   └── frontend/   # Interfaz web
├── docs/           # Ficha técnica, fuentes, registro de limpieza
├── README.md
└── .env.example
```

## Estado

En desarrollo durante la Misión: Código Formosa (noviembre de 2026). Las instrucciones de instalación y uso se agregarán a medida que el prototipo esté listo.

## Equipo

**SpaidyCode · Equipo 5** — UTN, Extensión Áulica Formosa.

## Licencia y datos

Los datos pertenecen a sus respectivas fuentes y se citan en `docs/`. Este prototipo no es una herramienta oficial ni reemplaza los reportes de los organismos competentes.
