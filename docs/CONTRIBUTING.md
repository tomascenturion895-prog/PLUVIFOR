# Cómo trabajamos

Reglas cortas para que cinco personas (y varias herramientas de IA) trabajen a la vez sin pisarse ni romper nada.

## 1. Ramas

- Tres ramas de larga vida, que **nunca se pisan con push forzado**:
  - `qa`: donde se integra y se prueba todo. **Es la base de los PR de cada tarea.**
  - `main`: lo que se entrega. Siempre funciona. Recibe `qa` por Pull Request en cada hito, y de ahí salen las etiquetas (`v0.9-nucleo`, `v1.0`).
  - `develop`: espejo de `qa`. Hoy no tiene trabajo propio: se mantiene alineada con `qa` por Pull Request (`qa` → `develop`) para que no diverja.
- Flujo real: **rama de tarea → `qa` → `main`**. Nadie sube directo a `qa`, `develop` ni `main`: todo entra por Pull Request.
- Después de una etiqueta de entrega, a `main` solo entran arreglos.
- Una rama por tarea de Jira, creada desde `qa` actualizada:

```
feature/SCRUM-<número>-descripcion-corta      # funcionalidad nueva
fix/SCRUM-<número>-descripcion-corta          # corrección de un error
docs/SCRUM-<número>-descripcion-corta         # solo documentación
```

Ejemplo: `feature/SCRUM-31-catalogo-estaciones`.

- Una rama vive uno o dos días como máximo. Si se alarga, se divide la tarea.

## 2. Commits

Formato: `tipo: descripción en presente (SCRUM-n)`

| Tipo | Cuándo |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de un error |
| `test` | Tests nuevos o cambios en tests |
| `docs` | Documentación |
| `refactor` | Cambio interno sin cambiar el comportamiento |
| `chore` | Configuración, dependencias, herramientas |

Ejemplos:

```
feat: endpoint de series diarias por estación (SCRUM-35)
fix: un día sin fila ya no se devuelve como 0 mm (SCRUM-35)
test: casos de ceros prolongados 424 vs 425 (SCRUM-33)
```

Commits chicos y frecuentes. Un commit = una idea.

## 3. Pull Requests

1. Subir la rama y abrir el PR contra `qa` con el título `[SCRUM-n] Qué hace`.
2. Completar la plantilla: qué hace, tarea, cómo probarlo y el Definition of Done.
3. **Una persona distinta de quien lo escribió lo revisa y aprueba.** Mínimo 1 aprobación.
4. Los checks automáticos (lint, tests, build) tienen que estar en verde.
5. Se integra con **Squash and merge** en las tareas, para que `qa` quede legible. Los PR de `qa` a `main` y de `qa` a `develop` se integran con **Merge commit** (no con squash), así las ramas no divergen.
6. Se borra la rama después de integrar.

Quien revisa mira: ¿cumple el «Hecho cuando»?, ¿hay tests?, ¿un hueco puede terminar como 0 mm?, ¿hay algún secreto?, ¿se metió algo de otro desafío?

## 4. Definition of Done

Una tarea está terminada cuando:

- [ ] Cumple el «Hecho cuando» escrito en Jira.
- [ ] Tiene tests (como mínimo el caso feliz y un caso de entrada inválida) y pasan.
- [ ] El lint y el build pasan.
- [ ] Un hueco de datos nunca se muestra ni se guarda como 0 mm.
- [ ] Lo observado, lo de referencia y lo estimado están separados.
- [ ] No hay secretos, claves ni archivos `.env` en el cambio.
- [ ] La leyenda «PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial» sigue visible (si toca la interfaz).
- [ ] La documentación se actualizó si cambió algo que otros usan.
- [ ] La tarea de Jira está en «Hecho» y el PR está integrado.

## 5. Reglas de oro del proyecto

1. **Un hueco no es 0 mm.** «Sin dato» y «cero» son cosas distintas, en la base, en la API y en pantalla.
2. **Observado, referencia y estimado van separados**, siempre con su fuente.
3. **Fecha de corte de los datos: 31/10/2026.** No se mezclan datos posteriores.
4. **Todo dato lleva su fuente** y su categoría.
5. **No se inventa nada.** Si falta un dato (por ejemplo, coordenadas), se deja vacío y se marca como pendiente.
6. **Alcance:** solo lluvia (Desafío 2). No se agregan alturas de ríos, riesgo, evacuaciones ni atajaderos.

## 6. Trabajo con herramientas de IA

Cada integrante usa su herramienta (Claude, Antigravity con Gemini, opencode). Para que todas hagan lo mismo:

- Leen `AGENTS.md` (la fuente de verdad del contexto del proyecto) antes de generar código.
- **Quien pide el código es responsable de lo que entra**: se lee, se prueba y se entiende antes de abrir el PR.
- La IA no inventa datos, endpoints ni dependencias: si algo no existe, se pregunta.
- Nunca se pegan claves, tokens ni datos personales en un chat de IA.

## 7. Qué hacer cada día

1. `git checkout qa && git pull`
2. Crear la rama de la tarea.
3. Trabajar, probar y hacer commits chicos.
4. Subir la rama y abrir el PR.
5. Revisar al menos un PR de otra persona.
6. Actualizar el estado de la tarea en el tablero.

## 8. Protección de `main` (configuración en GitHub)

En *Settings → Branches → Add branch ruleset* para `main` y `qa` (y `develop`):

- Requerir Pull Request antes de integrar, con 1 aprobación.
- Requerir que los checks de CI estén en verde (se activa cuando el CI esté funcionando).
- Bloquear los pushes directos.
