# Series de lluvia del SIGA (INTA) · estaciones de Formosa

PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Fuente: SIGA, Sistema de Información y Gestión Agrometeorológica del INTA, https://siga.inta.gob.ar
Consultado: 16/11/2026 · Categoría: OBSERVADO · Unidad: milímetros (mm) por día
Fecha de corte del kit: 31/10/2026 (ninguna de estas series llega a esa fecha)

## Archivos

| Archivo | Contenido |
|---|---|
| `estaciones_siga_formosa.csv` | Las tres estaciones que el SIGA tiene en Formosa, con coordenadas y período |
| `lluvia_diaria_siga_formosa.csv` | Una fila por estación y por día de calendario, incluidos los días sin dato |
| `descargar_siga.py` | Descarga las respuestas originales del SIGA a `original/` |

## Qué cubre el CSV de lluvia

| Estación (id SIGA) | Período incluido | Días | Con dato | Sin fila | Fila sin valor | mm acumulados |
|---|---|---|---|---|---|---|
| El Colorado convencional (51) | 01/01/2013 a 28/06/2015 | 909 | 878 | 0 | 31 | 3.460,1 |
| El Colorado automática (424) | 07/10/2013 a 07/12/2022 | 3.349 | 2.693 | 394 | 262 | 6.867,95 |
| Bartolomé de las Casas (425) | 12/12/2013 a 24/03/2023 | 3.390 | 1.694 | 1.624 | 72 | 5.908,0 |

La estación 51 tiene datos desde 1960 (20.268 días); acá solo está el tramo desde 2013.
La serie completa se obtiene ejecutando `descargar_siga.py`.

## Columnas

- `mm_pluviometrica`: campo `precDiaPlub` del SIGA. Es la lluvia del día que usa la herramienta.
- `mm_cronologica`: campo `precDiaCrono` del SIGA (solo estaciones automáticas).
- `estado`: `dato` (hay valor, puede ser 0), `sin_fila` (el SIGA no devuelve ese día),
  `fila_sin_valor` (el SIGA devuelve el día con la lluvia vacía). Los dos últimos son huecos, no ceros.
- `bandera`: `ceros_prolongados` cuando hay 60 o más días seguidos con 0 mm.

## Tratamiento aplicado

| Qué se hizo | Por qué | Filas afectadas |
|---|---|---|
| Se pidió al SIGA en ventanas de dos años | El servidor corta en 1.000 filas por pedido | todas |
| Se armó el calendario completo de cada estación | Para que los días ausentes queden visibles | 2.018 días `sin_fila` |
| Los valores vacíos quedaron vacíos | Un día sin registro no es un día sin lluvia | 365 días `fila_sin_valor` |
| Se redondeó a 2 decimales | El SIGA trae hasta 6 decimales en algunas filas | pocas |
| No se corrigió ni completó ningún valor | Regla del kit | 0 |

## Lo que hay que saber antes de usar estos datos

1. **Ceros que no son creíbles.** La estación 424 registra 0 mm durante 281 días seguidos,
   del 20/09/2015 al 26/06/2016. En ese mismo período la estación 425, a unos 100 km,
   registró 1.265 mm. El SIGA los informa como ceros, no como vacíos. Quedan marcados con
   la bandera `ceros_prolongados` y no deben sumarse como "no llovió".
2. **Las dos columnas de lluvia cierran el día a horas distintas.** El mismo evento suele
   aparecer un día en `mm_pluviometrica` y al día siguiente en `mm_cronologica`
   (por ejemplo, en la 424, 55,25 mm el 07/01/2014 en una y 55,25 mm el 08/01/2014 en la otra).
3. **La estación convencional fecha la lluvia un día después que la automática.**
   El mismo evento figura el 11/04/2014 en la 51 (143 mm) y el 10/04/2014 en la 424 (138 mm).
   Comparar día contra día entre redes da diferencias que no son reales.
4. **Totales anuales redondos en la serie larga de la 51:** 600 mm en 1968, 1.000 mm en 1997
   y 1.500 mm en 1998. Conviene revisarlos antes de usar esos años.

## Cómo se verificó

Los conteos de filas, de vacíos y de días con lluvia, y las sumas anuales de las dos columnas,
coinciden con los calculados sobre la respuesta del SIGA. Falta que el equipo ejecute
`descargar_siga.py` y guarde los originales: ese script no se pudo ejecutar desde el entorno
donde se preparó este paquete.
