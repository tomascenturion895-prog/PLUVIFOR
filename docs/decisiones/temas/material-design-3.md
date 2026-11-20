# Interfaz con Material Design 3

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Decisión del 19/11/2026 (Tomás Centurión): la interfaz sigue Material Design 3 (https://m3.material.io) y usa la librería oficial de Google.

## Dependencias nuevas (acordadas el 19/11/2026)

| Paquete | Versión | Licencia | Para qué |
|---|---|---|---|
| `@material/web` | 2.5.0 | Apache-2.0 | Componentes oficiales: onda (`md-ripple`), anillo de foco (`md-focus-ring`), progreso lineal (`md-linear-progress`) e ícono (`md-icon`) |
| `@fontsource/roboto` | 5.3.0 | OFL-1.1 | Tipografía Roboto servida desde la propia app, sin pedir nada a Google Fonts |
| `@material-symbols/svg-400` | 0.49.0 | Apache-2.0 | Íconos Material Symbols redondeados. Se importan de a uno como SVG, así que solo viajan los que se usan |

## Cómo se aplicó

- **Controles nativos:** los botones, campos y enlaces siguen siendo HTML nativo, así que la accesibilidad y las pruebas no cambian. Los componentes de Material se suman encima: `src/material/ondas.ts` agrega la onda y el anillo de foco a botones, pestañas, chips y tarjetas.
- **Color:** esquema M3 «tonal spot» generado con `material-color-utilities` desde el azul de PLUVIFOR `#0d5c6e`. Esa herramienta se usó solo para calcular los valores y no queda en el proyecto.
- **Escalas:** tipografía, forma, elevación y estados de M3 están en `src/material.css`.
- **Colores de datos sin cambios:** escala de lluvia, insignias observado, referencia y estimado, y el rayado de «sin dato».
