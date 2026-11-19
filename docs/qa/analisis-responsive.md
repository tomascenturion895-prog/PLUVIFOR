# Análisis responsive y pruebas e2e (SCRUM-71 y SCRUM-73)

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Fecha: 19/11/2026. Hecho con un Chrome de escritorio simulando pantallas y toques; **no se probó en celulares reales**. Eso sigue pendiente para una persona del equipo (ver «Qué no cubre»).

## Cómo correr las pruebas e2e

Desde `apps/frontend`, con el backend instalado (`apps/backend`, ver `docs/ENTORNO.md`):

```bash
npm ci
npx playwright install chromium     # una sola vez (o E2E_CHROME_PATH=/ruta/a/chrome)
npm run test:e2e
```

La configuración (`playwright.config.ts`) levanta sola la API en el puerto 8100 con una base de demo en un archivo temporal (`reset-demo`: 3 estaciones del SIGA/INTA, 7.648 días, sin internet) y la interfaz en el 5273, para no pisar lo que ya tengas corriendo. Variables opcionales: `E2E_PYTHON` (intérprete de Python con el entorno del backend), `E2E_CHROME_PATH` y `E2E_NO_SANDBOX=1` (para máquinas sin entorno gráfico).

Se corre el mismo archivo (`e2e/pluvifor.spec.ts`) en tres tamaños: **escritorio 1280×800, tableta 768×1024 y celular 360×740 con toque**. Son 26 pruebas por tamaño; 76 corren y 2 se saltan a propósito (la de 44 px solo aplica a celular).

## Qué verifican

| Tema | Prueba |
|---|---|
| Regla del hueco | La estación 424 sin filas en los últimos 90 días muestra «sin dato», «0 de 90» y la advertencia de cobertura baja, no 0 mm. |
| Racha de ceros | En 2015-09-20 a 2016-06-26 la 424 muestra advertencia de racha y la 425 su acumulado real (1.265 mm). |
| Leyenda | La leyenda de prototipo está en las 8 pantallas. |
| Parte pluvial | Se genera con fuente y fecha de corte (31/10/2026). |
| Importar | Sin clave de administración, «Auditar» y «Confirmar carga» están deshabilitados. |
| Mapa | Se dibuja y aclara que el color no es un total departamental. |
| Navegación | Inicio, menú y página de error en español. |
| Responsive | Sin scroll horizontal en las 8 pantallas; en celular, botones y campos de al menos 44 px en Estación, Parte e Importar. |

## Matriz de desborde (medida con Chrome)

Ancho de la página contra ancho de la ventana, en 8 pantallas (Inicio, Mapa, Estación, Comparador, Parte, Importar, Salud, Ayuda) y 8 anchos: 320, 360, 412, 600, 768, 1024, 1280 y 1920 px. **Resultado después del arreglo: ninguna combinación desborda (64 de 64 sin scroll horizontal).**

## Lo que se encontró y se corrigió

**Menú desbordado en tableta (768 y 900 px).** Antes, en todas las pantallas el ancho llegaba a 1007 px con una ventana de 768. Causa: desde 720 px el encabezado pasa a una fila con `display: flex` y el menú no podía achicarse (le faltaba `min-width: 0`), así que empujaba toda la página. Arreglo, solo CSS en `src/index.css`: el menú se achica y, desde 720 px, pasa a dos filas en lugar de cortarse. Sin el arreglo, 8 pruebas de tableta fallan; con él, pasan.

## Lo que se vio y no se tocó

- **Pie fijo.** En celular la leyenda de prototipo ocupa dos líneas y tapa cerca de 70 px del contenido que pasa por detrás. Es la leyenda obligatoria y tiene que estar siempre visible; no se cambió. Alternativa a decidir: acortar el texto en celular.
- **Menú en celular (menos de 720 px).** Se desplaza de costado dentro de su propia franja: «Comparador» aparece cortado a 360 px. Es intencional, pero no es obvio que haya más opciones.
- **Formato de fecha.** Los campos de fecha usan el formato del navegador; con un navegador en inglés aparece mes/día/año.
- **Comparador y Salud de la red** siguen diciendo «Esta pantalla está en construcción». Las pruebas de tamaño cubren solo esa vista provisoria.
- **Fecha por defecto de la ficha.** La ficha de estación abre en los últimos 90 días hasta el corte y no toma `from` ni `to` de la dirección, así que no se puede compartir un enlace con el período.
- **Mapa en celular.** El mapa ocupa casi toda la pantalla y los filtros quedan arriba; funciona, pero cuesta recorrer la página con el dedo sobre el mapa.

## Qué no cubre

- Celulares y tabletas reales (rendimiento, teclado en pantalla, orientación, navegadores de Apple), que son lo que pedía SCRUM-71 en su forma original. Se reemplazó por esta simulación por decisión del equipo (19/11) y **hay que verificarlo con el pulgar en al menos un celular antes de la demo**.
- Otros navegadores: solo Chrome.
- Flujos que escriben datos (confirmar una carga con clave): no se prueban de punta a punta para no manejar claves.
- Accesibilidad completa: ver `docs/qa/auditoria-celular.md` (axe-core, hecha aparte).
