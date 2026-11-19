# Catálogo de estaciones del prototipo

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Tarea: SCRUM-31 · Armado: 19/11/2026 · Archivo: `estaciones.csv` · Se regenera con `python docs/datos/generar_estaciones.py` (solo biblioteca estándar; da siempre el mismo resultado).

## Qué contiene (52 filas, en tres grupos que no se mezclan)

| `estado_catalogo` | Filas | Qué son | Categoría | Se carga en la base |
|---|---|---|---|---|
| `real_cargada` | 3 | Estaciones del SIGA/INTA (51, 424 y 425) | observado | Sí, con `import-stations` desde `estaciones_siga_formosa.csv` |
| `candidata_licencia_pendiente` | 15 | Estaciones del INA (`ina_estaciones_formosa.csv`) | observado | **No** hasta confirmar la licencia y que sus series existan |
| `simulada` | 34 | Estaciones **de ejemplo** que ocupan el lugar de las 34 provinciales | simulado | **No** (ver abajo) |

## Las 34 simuladas: qué son y por qué están

La lista de las 34 estaciones provinciales no está disponible (SCRUM-28, preguntas a la mentoría). Para poder mostrar el mapa, la regla de estaciones vecinas y la cobertura a escala provincial, el prototipo usa 34 estaciones **inventadas y marcadas como tales**:

- Nombre «Estación simulada NN · Dpto. X», tipo «Simulada (ejemplo)», categoría `simulado`, `coords_status` = `simulada`, y una nota que dice que no es una estación real.
- **Cómo se ubican:** sobre una grilla de 0,05° dentro del contorno de la provincia (capa del IGN del repositorio), de a una, el punto más alejado de las estaciones ya existentes, con un margen al borde de 0,15°. Es decir, rellenan los huecos de la red real. El departamento sale de la capa de departamentos del IGN.
- **Qué no tienen:** no tienen localidad, altura ni lluvia. No se inventó ninguna serie: una estación simulada sin datos se vería «sin dato», nunca 0 mm.
- **Qué pasa con una versión real:** quien tome el prototipo reemplaza estas filas por la lista oficial y carga datos reales. El resto del sistema no cambia.

Las simuladas no se suman ni se promedian con lo observado (regla 2 de `AGENTS.md`).

## Por qué el catálogo no se carga con `import-stations`

El importador del SIGA no distingue grupos: asignaría a todas las filas la fuente SIGA y marcaría como «verificadas» las coordenadas de cualquiera que tenga latitud y longitud. Cargar las simuladas así las haría pasar por observadas. Por eso el archivo usa la columna `codigo` y no `estacion_id`: el importador lo rechaza por columnas faltantes (hay una prueba que lo comprueba) y no se carga por error.

Para sumar las simuladas a la base hace falta una decisión del equipo: un conector propio con fuente `provincial_simulada`, categoría no observada y un estado de coordenadas «simulada» (hoy solo existen `verificada` y `pendiente`, lo que implica una migración). No se hizo sin acordarlo.

## Pendiente

- Lista oficial de las 34 estaciones provinciales con coordenadas (SCRUM-28 / mentoría): reemplaza a las simuladas.
- Licencia del INA y confirmación de que tiene lluvia diaria utilizable (ver `docs/fuentes/README.md`; los dos informes del INA se contradicen).
- Tres estaciones del INA «Bermejo - …» están sobre el límite provincial: quedan con coordenadas `pendiente`.
- Las estaciones del INA 788, 851 y 1462 parecen ser las 424, 425 y 51 del SIGA (a confirmar): no se fusionaron.
