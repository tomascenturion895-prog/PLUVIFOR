# Frontend · PLUVIFOR

Interfaz web del reporte pluvial de Formosa, en React + TypeScript + Vite.

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

## Requisitos

- Node.js 22 o superior

## Instalar y ejecutar

Desde `apps/frontend`:

```bash
npm ci
npm run dev        # http://localhost:5173
```

En desarrollo, las llamadas a `/api` se reenvían al backend (por defecto `http://localhost:8000`; se cambia con `VITE_API_URL`).

## Comandos

| Comando                           | Qué hace                                                      |
| --------------------------------- | ------------------------------------------------------------- |
| `npm run dev`                     | Servidor de desarrollo                                        |
| `npm run build`                   | Revisa los tipos y genera la versión de producción en `dist/` |
| `npm test`                        | Corre las pruebas (Vitest + Testing Library)                  |
| `npm run lint`                    | Revisa el código con Oxlint                                   |
| `npm run format` / `format:check` | Da formato / verifica el formato con Prettier                 |

## Tecnologías

React 19, TypeScript, Vite, React Router, Recharts (gráficos), Leaflet y React-Leaflet (mapa), Vitest, Testing Library, Oxlint y Prettier.

## Reglas del proyecto

- La leyenda de prototipo (`src/constants.ts`) debe verse en todas las pantallas.
- Un hueco de datos nunca se muestra como 0 mm.
- Textos de la interfaz en español.

Ver `AGENTS.md` y `docs/CONTRIBUTING.md`.
