# Pruebas de componentes: un hueco nunca se muestra como cero

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-56. Las pruebas del frontend (Vitest y Testing Library, 99 pruebas en 9 archivos) ya cubren los puntos de la tarea. Este documento dice qué prueba cada punto, comprueba que **mostrar 0 para un hueco hace fallar pruebas** y deja anotado lo que se encontró. No se agregó código de prueba nuevo porque no faltaba nada del criterio.

## Qué prueba cada punto de la tarea

| Punto | Prueba (archivo · nombre) |
|---|---|
| Insignia de dato | `Insignias.test.tsx` · `dato` |
| Insignia de sin dato (`sin_fila`) | `Insignias.test.tsx` · `sin fila se muestra como «Sin dato»` |
| `fila_sin_valor` se distingue de `sin_fila` | `Insignias.test.tsx` · `fila sin valor se distingue de sin fila` |
| No depende solo del color | `Insignias.test.tsx` · `lleva símbolo propio y descripción accesible` |
| Observado, referencia y estimado | `Insignias.test.tsx` · `insignias de categoría` (los tres textos) y `cada categoría tiene una clase distinta` |
| Las 6 advertencias | `Insignias.test.tsx` · `hay una por cada una de las 6 advertencias de comparabilidad` |
| Mensaje de la API y código desconocido | `Insignias.test.tsx` · `si la API manda un mensaje…` y `un código desconocido igual se muestra` |
| `mm` nulo muestra «sin dato» | `Insignias.test.tsx` · `textoMm › un hueco es «sin dato», nunca 0`; `Estacion.test.tsx` · `en la tabla los huecos son huecos y un cero real es 0 mm` |
| Un cero real sí es 0 mm | `Insignias.test.tsx` · `un cero real sí se muestra como 0 mm` |
| Período sin ningún dato | `Estacion.test.tsx` · `un período sin ningún día con dato muestra «sin dato», no 0 mm` |
| Gráfico de la serie | `SerieDiaria.test.ts` · `un hueco no tiene milímetros: la barra no se dibuja` y `un cero real se dibuja como 0` |
| Estado de carga | `Estados.test.tsx` · `Cargando avisa con un estado accesible` |
| Estado de error y reintentar | `Estados.test.tsx` · `ErrorEstado muestra el mensaje como alerta` y `ofrece reintentar` |
| Parte pluvial, importación | `Parte.test.tsx`, `Importar.test.tsx` |
| Se corren en el CI | `.github/workflows/ci.yml` ejecuta `npm test` en cada PR |

## Comprobación: mostrar 0 para un hueco hace fallar una prueba

Se rompió el código a propósito, una vez por vez, se corrió `npm test` y se restauró el original.

| # | Rotura | Dónde | Resultado |
|---|---|---|---|
| M1 | Un `mm` nulo se muestra como «0 mm» en lugar de «sin dato» | `src/components/insignias-datos.ts`, `textoMm` | **Fallan 3 pruebas** (una de `Insignias.test.tsx` y dos de `Estacion.test.tsx`) |
| M2 | Un día sin dato entra al gráfico con 0 mm en lugar de nulo | `src/components/serie-diaria-datos.ts`, `armarPuntos` | **Falla 1 prueba**: `un hueco no tiene milímetros: la barra no se dibuja` |

Son dos roturas elegidas a mano, no una herramienta automática de mutaciones.

## Lo que se encontró

- **Un valor muy chico se muestra como «0 mm».** `textoMm` redondea a un decimal: 0,04 mm sale como «0 mm», y 0,05 mm sale como «0,1 mm». No es un hueco, pero un registro de lluvia real que se muestra como cero se parece a lo que la regla quiere evitar. **No aparece en los datos actuales**: ningún valor del SIGA cargado está entre 0 y 0,05 mm. No lo cambié ni lo fijé con una prueba, porque es una decisión de texto de la interfaz (por ejemplo, mostrar «menos de 0,1 mm»). Queda para el equipo.
- No hay prueba del texto «sin dato» en el mapa ni en el comparador: esas pantallas todavía son de marcador (SCRUM-50 y 51).
