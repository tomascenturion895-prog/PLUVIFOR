# Capas geográficas de PLUVIFOR

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Capas de referencia cartográfica para el mapa y la maqueta de Formosa (SCRUM-24). No contienen datos de lluvia.

| Archivo                                     | Contenido                                                                                          | Entidades |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------- |
| `formosa_provincia.geojson`                 | Límite de la provincia                                                                             | 1         |
| `formosa_departamentos.geojson`             | Departamentos (Bermejo, Formosa, Laishi, Matacos, Patiño, Pilagás, Pilcomayo, Pirané, Ramón Lista) | 9         |
| `formosa_cursos_agua_perennes.geojson`      | Cursos de agua perennes                                                                            | 181       |
| `formosa_cursos_agua_intermitentes.geojson` | Cursos de agua intermitentes                                                                       | 574       |

## Fuente

- **Instituto Geográfico Nacional (IGN)**, servicio WFS `https://wms.ign.gob.ar/geoserver/ows`.
- Capas: `ign:provincia`, `ign:departamento`, `ign:lineas_de_aguas_continentales_perenne` y `ign:lineas_de_aguas_continentales_intermitentes`.
- Fecha de descarga: 19/11/2026.
- Categoría: referencia cartográfica (no es observado ni estimado).

## Licencia

**Pendiente de confirmar.** El IGN publica su información geoespacial para uso público con cita de la fuente; no se verificó el texto exacto de la licencia. Hasta confirmarlo, citar siempre «Fuente: Instituto Geográfico Nacional (IGN)».

## Cómo se prepararon

- Provincia y departamentos: filtro `in1 LIKE '34%'` (código de Formosa), propiedades reducidas a `id`, `nombre`, `nombre_completo`, `provincia` y `fuente`.
- Cursos de agua: tomados dentro del cuadro de la provincia y conservados los que tienen al menos un vértice dentro del límite; **no se recortan** exactamente en el límite: se descartan los vértices a más de 0,5° del cuadro de la provincia, así que continúan un tramo hacia los países y provincias vecinas.
- Coordenadas redondeadas a 4 decimales y geometría simplificada (Douglas-Peucker): 0,001° (~110 m) en polígonos y 0,003° (~330 m) en líneas, para que carguen en menos de 2 s.
- Al simplificar cada polígono por separado, los bordes compartidos entre departamentos pueden quedar con pequeñas diferencias (menos de ~110 m). Sirve para visualizar, no para medir superficies ni asignar una estación a un departamento con precisión.
- No se agregaron coordenadas de estaciones: siguen pendientes las que no tienen fuente.
