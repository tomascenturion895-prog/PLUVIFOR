# Insignias

Componentes en `Insignias.tsx`; códigos de advertencia y `textoMm` en `insignias-datos.ts`. Cada una muestra **texto, un símbolo y una descripción**: el color nunca es la única señal.

> Regla central: **un hueco no es 0 mm**. «Sin dato» y «Fila sin valor» tienen su propio gris con borde punteado y nunca el texto, el símbolo ni el color de un dato.

## Estado del día: `<InsigniaEstado estado="…" />`

| `estado` (API)   | Se ve                | Cuándo                                 |
| ---------------- | -------------------- | -------------------------------------- |
| `dato`           | ● **Dato**           | hay una medición (puede ser 0 mm real) |
| `sin_fila`       | ∅ **Sin dato**       | la fuente no tiene ese día             |
| `fila_sin_valor` | ◌ **Fila sin valor** | la fuente tiene el día pero sin valor  |

## Categoría: `<InsigniaCategoria categoria="…" />`

| `categoria`  | Se ve            | Nota                         |
| ------------ | ---------------- | ---------------------------- |
| `observado`  | ▣ **Observado**  | medido                       |
| `referencia` | ◆ **Referencia** | nunca se suma a lo observado |
| `estimado`   | ≈ **Estimado**   | calculado; borde de puntos   |

## Simulado: `<InsigniaSimulado />`

⚙ **Simulado**, con borde de guiones. Rotula las lecturas del simulador de dispositivos (SCRUM-94): no son de un sensor real y nunca se suman a lo observado, lo de referencia ni lo estimado.

## Advertencia: `<InsigniaAdvertencia codigo="…" mensaje="…" />`

Usa los `code` que devuelve la API. `mensaje` (opcional) es el texto de la API y pasa a ser la descripción.

| `codigo`                    | Texto                     |
| --------------------------- | ------------------------- |
| `horario_corte_distinto`    | Horario de corte distinto |
| `observado_vs_estimado`     | Observado vs. estimado    |
| `cobertura_despareja`       | Cobertura despareja       |
| `dato_sin_validar`          | Dato sin validar          |
| `ceros_prolongados`         | Racha de ceros            |
| `inconsistente_con_vecinas` | Inconsistente con vecinas |

Un código que no está en la tabla se muestra igual, con el mensaje de la API: una advertencia nunca se oculta.

## Milímetros: `textoMm(mm)`

`null` → `sin dato`. `0` → `0 mm` (un cero real). `12.5` → `12,5 mm`. Usalo siempre para mostrar la lluvia de un día.

## Accesibilidad

- El símbolo es decorativo (`aria-hidden`); el texto y la descripción los lee el lector de pantalla (`.sr-only`) y aparecen como `title`.
- Los colores tienen contraste suficiente sobre su fondo; además cada categoría cambia el estilo de borde (sólido, punteado, de puntos).

## Cómo agregar una insignia

Agregá su definición (clase, símbolo, texto y descripción) en `Insignias.tsx`, su color en `Insignias.css`, una prueba en `Insignias.test.tsx` y una fila en este archivo.
