# PLUVIFOR · Sistema de Diseño Visual y Reglas de Estilos

> **Fuente de verdad para el diseño de interfaz de PLUVIFOR.**
> Ningún componente, vista ni estilo nuevo debe romper estas reglas. Cualquier cambio de tema (ej. pasar de Radar Dark a Día Claro o viceversa) debe lograrse modificando exclusivamente las variables de `:root`, sin tocar los componentes individuales.

---

## 1. Principio Fundamental: Cero Colores Hardcodeados

**PROHIBIDO:** Escribir colores fijos en fondos, textos o bordes (como `background: #fff;`, `background: white;`, `color: #000;`, `border: 1px solid #ccc;`).
**OBLIGATORIO:** Usar siempre los tokens semánticos definidos en CSS Custom Properties.

Si un desarrollador o una IA escribe `background: #fff;` en un componente, ese componente quedará como un parche blanco ilegible cuando el sistema use un tema oscuro, ocultando texto blanco sobre fondo blanco.

---

## 2. Mapa de Variables Semánticas (Tokens)

Las vistas deben construirse empleando **únicamente** estas variables:

| Variable | Propósito | Radar Dark (actual) | Día / Claro (alternativa) |
|---|---|---|---|
| `--papel` | Fondo principal de la página (`body`, `#root`) | `#0b1322` | `#f8fafc` |
| `--superficie` | Tarjetas nivel 1, paneles (`.panel`), contenedores | `#131d2e` | `#ffffff` |
| `--superficie-elevada`| Tarjetas secundarias, dropdowns, `fieldset` | `#1e293b` | `#f1f5f9` |
| `--tinta` | Color de texto principal y títulos (`h1`, `h2`, `h3`) | `#f8fafc` | `#0f172a` |
| `--texto-suave` | Texto secundario, notas, captions, labels (`.nota`) | `#94a3b8` | `#475569` |
| `--borde` | Líneas divisorias, bordes de tarjetas e inputs | `#334155` | `#e2e8f0` |
| `--borde-suave` | Separadores internos sutiles | `#1e293b` | `#f1f5f9` |
| `--accu-orange` | Acento principal: llamadas a la acción, tabs activas | `#f05514` | `#f05514` |
| `--accu-orange-hover`| Hover en botones primarios | `#ff6a2b` | `#d94709` |
| `--accu-radar-blue` | Azul radar para gráficos de precipitación | `#0ea5e9` | `#0284c7` |
| `--radio` | Radio de esquinas para tarjetas y paneles | `0.75rem` (`12px`) | `0.75rem` (`12px`) |
| `--sombra` | Sombra estándar de elevación | `0 4px 16px -2px rgb(0 0 0 / 40%)` | `0 4px 16px -2px rgb(15 23 42 / 8%)` |

---

## 3. Guía de Componentes y Patrones

### A. Paneles y Tarjetas (`.panel`, `.hero`, `.resumen div`, `.capas`)
- **Fondo:** `background: var(--superficie);`
- **Borde:** `border: 1px solid var(--borde);`
- **Radio:** `border-radius: var(--radio);`
- **Sombra:** `box-shadow: var(--sombra);`
- **Títulos (`h3`):** `color: var(--tinta); font-weight: 700;`

### B. Formularios, Controles e Inputs (`select`, `input`, `textarea`)
- **Fondo:** Fondo oscuro `background: #0f172a;` (en modo oscuro) o `var(--papel)`.
- **Texto:** `color: var(--tinta);`
- **Borde:** `border: 1px solid var(--borde);`
- **Focus:** `border-color: var(--accu-orange); box-shadow: 0 0 0 3px rgba(240, 85, 20, 0.25); outline: none;`
- **Select Options:** Asegurarse de definir `option { background: ...; color: ...; }` para evitar que el navegador aplique un fondo blanco por defecto con texto blanco.

### C. Botones
1. **Primarios (`.acciones button`, `.boton-primario`):**
   - Fondo: `var(--accu-orange)`
   - Texto: `#ffffff`
   - Borde: `0`
   - Hover: `background: var(--accu-orange-hover); box-shadow: 0 4px 14px rgba(240, 85, 20, 0.45);`
2. **Secundarios / Filtros (`.atajos button`, `fieldset button`):**
   - Fondo: `var(--superficie-elevada)`
   - Texto: `var(--tinta)`
   - Borde: `1px solid var(--borde)`
   - Hover: `border-color: var(--accu-orange); color: #fff; background: rgba(240, 85, 20, 0.15);`
3. **Activos (`[aria-pressed='true']`):**
   - Fondo: `var(--accu-orange)`
   - Texto: `#ffffff`
   - Borde: `1px solid var(--accu-orange)`

### D. Tablas (`.tabla-scroll`, `.tabla-dias`)
- **Contenedor:** `background: var(--superficie); border: 1px solid var(--borde);`
- **Encabezados (`thead th`):** `background: var(--superficie-elevada); color: var(--texto-suave); font-weight: 700;`
- **Filas (`td`, `th`):** `border-bottom: 1px solid var(--borde); color: var(--tinta);`
- **Hover fila:** `background: rgba(255, 255, 255, 0.04);`

### E. Integración de Mapas y Gráficos (Leaflet & Recharts)
- Contenedor de mapa: `background: #0b1322;`
- Popups de Leaflet: `background: var(--superficie-elevada); color: var(--tinta); border: 1px solid var(--borde);`
- Tooltips de Recharts: `.recharts-default-tooltip { background: var(--superficie-elevada) !important; color: var(--tinta) !important; border: 1px solid var(--borde) !important; }`
- Cuadrícula de Recharts: `.recharts-cartesian-grid line { stroke: var(--borde) !important; }`

### F. Escenarios 3D y Maqueta (`Vista 3D` y `Maqueta`)
- **Etiquetas de departamento seleccionado (`.v3d-etiqueta-depto.es-elegida`):** Fondo oscuro sólido `#0f172a`, borde solar `2px solid var(--accu-orange)`, texto `#ffffff` en negrita con sombra y realce. NUNCA fondo blanco.
- **Rótulos SVG de departamentos (`.maqueta-nombre`):** Texto claro `#f8fafc` con trazo perimetral oscuro `#0f172a`. Al activarse el bloque, el trazo destaca en `var(--accu-orange)`.
- **Controles de cámara y escenario (`.v3d-segmentado`, pestañas):** Botones inactivos transparentes sobre panel oscuro; botón activo en `var(--accu-orange)` con texto `#ffffff`.

---

## 4. Inviolabilidad de las Reglas de Datos (AGENTS.md)

1. **La escala de lluvia NO se modifica:** La función `colorMm` en `map-helpers.ts` (escala ColorBrewer YlGnBu) es la referencia estándar de datos y está verificada por tests de regresión.
2. **Las insignias de datos (`Insignias.css`) se respetan:**
   - `dato`: punto sólido
   - `sin_fila` / `sin_valor`: rayado / gris / punteado (¡un hueco NO es 0 mm!)
   - `observado`: verde
   - `referencia`: violeta
   - `estimado`: naranja punteado
   - `simulado`: azul celeste rayado
3. **Leyenda obligatoria visible:**
   `PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial` siempre fija en el pie.
4. **Alto Contraste:**
   El selector `html[data-contraste='alto']` debe garantizar fondo `#fff`, tinta `#000` y bordes sólidos de alto contraste.

---

## 5. Cascada de Hojas de Estilo en `main.tsx`

El orden de importación en `apps/frontend/src/main.tsx` es estricto:
```typescript
import './index.css'        // Estructura y reset base
import './maqueta3d.css'    // Geometría SVG y 3D de maqueta
import './vista3d.css'      // Escenario Three.js
import './pulido.css'       // Animaciones y microinteracciones
import './material/registro'
import './material.css'     // Tokens Material 3
import './theme.css'        // IDENTIDAD VISUAL PLUVIFOR (gana precedencia)
```
Cualquier nueva regla de color o personalización debe agregarse en `theme.css`.

