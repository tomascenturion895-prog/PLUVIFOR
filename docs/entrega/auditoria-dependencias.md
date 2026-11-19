# Auditoría de dependencias

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Fecha de la auditoría: **19/11/2026** (rama `feature/SCRUM-70-informe-seguridad`, sobre el estado de los PR #29 a #41). Tarea: SCRUM-69.

## Resultado

| Parte | Herramienta | Resultado |
|---|---|---|
| Backend (`apps/backend/requirements.txt`, 5 directas, 25 con las transitivas) | `pip-audit` | **Sin vulnerabilidades conocidas** |
| Backend, desarrollo (`requirements-dev.txt`) | `pip-audit` | **Sin vulnerabilidades conocidas** |
| Frontend (`apps/frontend`, 218 paquetes: 51 de producción, 167 de desarrollo) | `npm audit` | **0 vulnerabilidades** (info 0, baja 0, moderada 0, alta 0, crítica 0) |
| API en Go (`apps/api-go/go.mod`) | — | **No aplica:** el directorio no existe (ver `docs/preguntas-citf.md`, pregunta 8) |

No hay nada marcado, así que no hay excepciones que aceptar.

## Versiones fijadas

- **Backend:** las cinco dependencias directas están fijadas con `==` (por ejemplo `fastapi==0.163.2`). Las **transitivas no están fijadas** en un archivo de bloqueo: se resuelven al instalar. Es un riesgo menor y aceptado para el prototipo; si se quisiera cerrarlo, se genera un `requirements.lock` con `pip-compile` (sería una herramienta nueva, por eso no se agregó sin consultar).
- **Frontend:** `package.json` usa rangos (`^`), pero `package-lock.json` fija cada versión y el CI instala con `npm ci`, que respeta el bloqueo y falla si no coincide con `package.json`.

## Cómo repetirla

```bash
# Backend (desde apps/backend, con el entorno virtual activo)
pip install pip-audit
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt

# Frontend (desde apps/frontend)
npm audit
```

## Límites de esta auditoría

- Las herramientas consultan bases públicas de vulnerabilidades conocidas el día en que se corren: **no** detectan fallas aún no publicadas y el resultado puede cambiar mañana. Conviene repetirla antes de publicar (SCRUM-79).
- Se corrió con Python 3.13 en el entorno de trabajo; el proyecto declara 3.12. Las versiones de las librerías son las mismas, pero un auditor de la entrega debería repetirla con 3.12.
- No se agregó la auditoría al CI para no tocar los flujos de GitHub Actions sin acordarlo. Es un siguiente paso razonable (`npm audit --audit-level=high` y `pip-audit` como pasos del workflow `ci.yml`).
