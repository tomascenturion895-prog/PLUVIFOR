# Vista 3D: exposición pluvial por departamento

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Decisión del 19/11/2026 (Tomás Centurión). Ruta `/vista-3d`.

## Por qué suma a la solución

Responde «¿dónde llovió fuerte?» sobre el mapa real de la provincia y lo cruza con dónde hay más ríos y riachos. Ayuda a mirar El Niño 2026/27 por departamento sin salirse del núcleo de lluvia. Toca un tema de «Requiere fundamento» (zonas expuestas a anegamiento), por eso queda escrito acá.

## Qué muestra (todo con datos reales)

- **Límites de departamentos y cursos de agua:** IGN, los mismos GeoJSON de `apps/frontend/public/geo`.
- **Lluvia:** serie diaria observada del SIGA/INTA para el período elegido.
- **Clase pluvial de una estación:**
  - alta si tuvo algún día de 100 mm o más;
  - media si tuvo alguno de 50 mm o más;
  - baja si no tuvo ninguno.
  Los días sin dato no cuentan como 0 mm. Una estación con racha de ceros (60 días o más) se descarta.
- **Clase pluvial del departamento:** la de su estación más lluviosa. Los milímetros de estaciones distintas no se suman ni se promedian.
- **Red hídrica:** kilómetros de cursos de agua perennes e intermitentes cada 100 km², repartidos en tercios entre los 9 departamentos. Es aproximada, porque las capas están simplificadas.
- **Exposición (categoría «estimado»):** tabla 3 × 3 de lluvia × red hídrica. Sin dato de lluvia no hay exposición: el departamento se dibuja rayado, nunca como «baja».
- **Departamento de cada estación:** el del catálogo. Si falta, se deduce por las coordenadas, solo cuando están verificadas; en ese caso la interfaz lo aclara.

## Lo que no es

No es una predicción de inundación ni un mapa de riesgo oficial. Falta el relieve, el suelo y el estado de los ríos. La altura de los bloques repite la clase; no es el relieve.

## Simulación de ciudad: descartada

Se probó una simulación de anegamiento sobre una ciudad con terreno inventado y se descartó el mismo día. No representa a Formosa y no sirve para medir nada real. Para hacerla sobre la ciudad real hacen falta:

- un modelo de elevación con licencia verificada (MDE-Ar del IGN o SRTM);
- una capa de manzanas o calles con licencia (por ejemplo, OpenStreetMap, ODbL).

## Dependencia nueva: three.js

- **Paquete:** `three` 0.187.0, más `@types/three` como dependencia de desarrollo. Licencia MIT. Acordado con Tomás el 19/11/2026.
- **Para qué:** WebGL, que el SVG de la maqueta no puede dar (girar, acercar, sombras).
- **Peso:** se carga solo al abrir `/vista-3d`, porque la ruta usa carga diferida (unos 157 kB comprimidos). El resto de las pantallas no lo descarga.
- **Sin WebGL:** la página avisa y la tabla de departamentos muestra los mismos datos.
