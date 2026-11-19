# Auditoría de celular y accesibilidad (360 px)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-67. Se revisaron las pantallas con Chrome a **360 px de ancho** (pantalla de celular, densidad 2, táctil), con datos reales del SIGA cargados, y se pasó **axe-core** (reglas WCAG 2.0 y 2.1 A y AA, más las buenas prácticas de axe). Se midió el desborde horizontal y el tamaño de los objetivos táctiles. El script de la auditoría no está en el repositorio (no se agregó una dependencia nueva).

**Lo que esta auditoría no es:** no reemplaza usar la herramienta con el pulgar en un celular real ni que una persona ajena lea los textos (los dos criterios de cierre de la tarea). Eso sigue pendiente.

## Qué se encontró y qué se arregló

| # | Hallazgo (antes) | Dónde | Arreglo |
|---|---|---|---|
| 1 | **La página se ensanchaba a 621 px** (en un celular, desplazamiento horizontal) por una advertencia con el mensaje en una sola línea | Ficha de estación | `Insignias.css`: la insignia de advertencia ahora parte el texto en líneas y no pasa del ancho |
| 2 | **Los campos de estación, fechas, clave y archivo medían 405 y 375 px** dentro de una columna de 328 px y ensanchaban la página (421 y 391 px) | Estación e Importar | `index.css`: columna con `minmax(0, 1fr)` y campos con `width: 100%` |
| 3 | Un botón de 21 px de alto («Ver historial») | Importar | `index.css`: todo botón mide al menos 44 px de alto |

Después de los arreglos, **ninguna pantalla desborda a 360 px** y todos los botones y campos miden al menos 44 px. Las pruebas del frontend (99), el lint, el formato y la compilación siguen pasando. Son cambios de presentación: no se tocó lógica de datos.

## Qué salió bien

- **axe-core: 0 infracciones** en las 10 direcciones revisadas (46 reglas aprobadas en la ficha de estación). La regla de contraste quedó «incompleta» en axe (no pudo decidirlo sola), por eso se calculó a mano.
- **Contraste calculado a mano:** los pares de color de las insignias dan entre 6,05 y 9,00 a 1 (AA pide 4,5), y el texto principal sobre el fondo, 14,25 a 1.
- Con el teclado se recorre el menú, el selector y los campos con el foco visible. (Un campo tiene el contorno propio de 3 px.)
- La página declara el idioma español.

## Lo que queda sin arreglar

1. **El título de la pestaña es el mismo en todas las pantallas** («PLUVIFOR · Reporte pluvial de Formosa»), y el único `h1` de cada página es «PLUVIFOR». Un lector de pantalla no distingue la pantalla por el título. Arreglarlo pide un cambio de código en cada página (un título por ruta), no solo de presentación: lo dejé para decidir.
2. **La advertencia de cobertura baja se ve dos veces**: una vez como insignia y otra como párrafo con el mismo texto. La API la manda con el código `cobertura_baja`, que no está entre los 6 de la interfaz, y entonces la insignia muestra el mensaje completo. Una solución es sumar un texto corto para ese código.
3. **El menú se corta a 360 px**: se ve «Comparad…» y el resto se alcanza desplazando. Funciona, pero no es evidente.
4. **El enlace «Volver al inicio»** de la página de error mide 20 px de alto (es un enlace dentro de una oración, que las pautas permiten).
5. **Mapa, comparador, salud de la red y ayuda** son pantallas de marcador (SCRUM-50 y 51): no tiene sentido auditarlas hasta que existan.

## Pendiente de personas

- Usar las pantallas principales con el pulgar en un celular real (SCRUM-71).
- Que una persona ajena lea cada texto y diga si lo entiende.
- Coordinar con el panel de accesibilidad (SCRUM-100).
- Una revisión con un lector de pantalla real.
