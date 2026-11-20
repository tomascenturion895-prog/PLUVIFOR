---
name: pluvifor-diseno-visual
description: Guía y reglas del sistema de diseño visual de PLUVIFOR (AccuWeather / Radar Dark). Úsala al modificar o crear componentes frontend, CSS, tarjetas, formularios o vistas para asegurar consistencia cromática, evitar colores hardcodeados y no romper temas.
---

# Skill: Sistema de Diseño Visual PLUVIFOR

Esta skill establece las reglas de diseño para la interfaz de **PLUVIFOR** (estilo AccuWeather / Centro Meteorológico / Radar Dark).

## Cuándo activar esta skill
- Al agregar nuevas vistas, componentes o maquetas en `apps/frontend`.
- Al modificar archivos de estilos (`theme.css`, `material.css`, `index.css`, `maqueta3d.css`, etc.).
- Al ajustar botones, paneles, tarjetas, tablas, gráficos o controles de formulario.
- Cuando se decida alternar o evolucionar temas (ej. modo oscuro radar vs. modo claro día).

---

## Reglas Inquebrantables de Estilo

1. **PROHIBIDO hardcodear colores:**
   - ❌ Nunca uses `background: #fff;` o `background: white;`.
   - ❌ Nunca uses `color: #000;` o `color: black;`.
   - ❌ Nunca uses `border: 1px solid #ccc;`.
   - ✅ Usa siempre tokens semánticos: `var(--papel)`, `var(--superficie)`, `var(--superficie-elevada)`, `var(--tinta)`, `var(--texto-suave)`, `var(--borde)`, etc.

2. **Tokens semánticos principales:**
   - Fondo de página: `var(--papel)`
   - Tarjetas y paneles principales (`.panel`, `.hero`, `.resumen div`): `var(--superficie)`
   - Paneles secundarios y fieldsets (`fieldset`, dropdowns, `.tabla-scroll thead th`): `var(--superficie-elevada)`
   - Títulos y texto prioritario (`h1`, `h2`, `h3`, números KPI): `var(--tinta)`
   - Texto secundario y notas (`.nota`, `small`, labels): `var(--texto-suave)`
   - Bordes y divisores: `var(--borde)` y `var(--borde-suave)`
   - Acento primario (CTAs, pestañas activas, foco): `var(--accu-orange)`
   - Acento de precipitación en gráficos: `var(--accu-radar-blue)`

3. **Formularios y controles:**
   - Selects e inputs deben tener fondo oscuro coherente (`#0f172a`), texto `var(--tinta)` y borde `var(--borde)`.
   - Los elementos `<option>` deben tener color y fondo explícitos para no heredar fondos blancos de los navegadores.
   - Anillos de foco: `outline: 2px solid var(--accu-orange); outline-offset: 2px;`.

4. **Integridad de datos (AGENTS.md):**
   - La escala de lluvia en mapas (`colorMm` con ColorBrewer YlGnBu) no se altera.
   - Las insignias de estado del dato (`InsigniaEstado`, `InsigniaCategoria`) conservan su semántica: un día sin dato **no es 0 mm**.
   - La leyenda de prototipo debe permanecer fija y visible en el pie de página.
   - Modo de alto contraste (`html[data-contraste='alto']`) debe mantenerse 100% accesible (fondo blanco puro, tinta negra pura).

5. **Lugar de personalización:**
   - Todo cambio de tema o estilo debe concentrarse en `apps/frontend/src/theme.css`, que es la hoja con mayor jerarquía y precedencia en la cascada.

6. **Etiquetas y selección en mapas 3D:**
   - La píldora de departamento seleccionado (`.v3d-etiqueta-depto.es-elegida`) siempre lleva fondo oscuro `#0f172a`, borde `var(--accu-orange)` y texto `#ffffff`. Nunca fondo blanco.

