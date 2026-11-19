# Ficha de fuentes

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

De dónde sale cada dato de PLUVIFOR, con qué categoría, con qué condiciones y qué falta confirmar. Tarea SCRUM-44. Fecha de corte de los datos: **31/10/2026**.

**Cómo leerla.** «Pendiente» quiere decir que **no está verificado**: no se completó de memoria ni por suposición (regla 5 del proyecto). Las licencias que figuran como confirmadas tienen el enlace donde se leyeron. Las demás están como pendientes de confirmar con el organismo.

## Resumen

| Fuente | Aporta | Categoría | Corte del «día» | Licencia / condiciones | Estado en el proyecto |
|---|---|---|---|---|---|
| SIGA / INTA | Lluvia diaria, estaciones 51, 424 y 425 | `observado` | 09:00 (12-12 UTC) en la convencional; **la automática y las dos columnas de lluvia cierran distinto: ver más abajo** | **Pendiente de confirmar** (ver nota) | Cargada |
| INA (Alerta Hidrológico) | Lluvia diaria de 15 estaciones listadas en y junto a Formosa | `observado` (a confirmar al cargar) | 12 UTC (09:00 de Argentina) | **Pendiente de confirmar** | Solo listado; **no se descargaron valores** |
| Red provincial | Lluvia diaria de estaciones de la provincia | `observado` | 07:00 a 07:00 | **Pendiente** | **Sin cargar y sin fuente verificada** |
| UPCA | Lluvia diaria | `observado` | 07:00 a 07:00 | **Pendiente** | **Sin cargar y sin fuente verificada** |
| SNIH | Lluvia diaria | `observado` | 07:00 a 07:00 | **Pendiente** | **Sin cargar y sin fuente verificada** |
| SMN | Normal mensual 1991-2020, estación Formosa Aero | `referencia` | No aplica (promedio de 30 años) | CC BY 2.5 AR (leída en el repositorio del SMN) | Cargada (SCRUM-60) |
| CHIRPS v3 | Lluvia estimada por satélite y estaciones | `estimado` | No verificado | **Dos textos distintos: ver nota** | **Sin cargar** (SCRUM-43) |

Los cortes de la red provincial, UPCA, SNIH, SMN e INTA convencional son los que fija `AGENTS.md` (regla 6). Al comparar redes con cortes distintos la interfaz muestra la advertencia de horario de corte.

## SIGA / INTA

- **Qué es:** Sistema de Información y Gestión Agrometeorológica del INTA, https://siga.inta.gob.ar
- **Qué hay cargado:** tres estaciones de Formosa, `docs/datos/lluvia_diaria_siga_formosa.csv` (7.648 filas). Detalle, conteos y tratamiento en `docs/datos/LEEME_siga.md`. Consultado el 16/11/2026 y los originales se bajaron el 18/11/2026.
- **Cobertura:** estación 51 (2013 a 2015 en el CSV; la serie completa va desde 1960), 424 (2013 a 2022) y 425 (2013 a 2023). Ninguna llega al 31/10/2026.
- **Limitaciones:**
  - La 424 marca 0 mm durante 281 días seguidos (20/09/2015 a 26/06/2016) mientras la 425 registra 1.265 mm: se advierte, no se da por bueno.
  - La estación convencional fecha la lluvia un día después que la automática, y las dos columnas de lluvia de la automática cierran a horas distintas.
  - La 425 tiene 1.624 días sin fila y el SIGA no devolvió nada para 2019 y 2020.
  - Totales anuales redondos en la serie larga de la 51 (1968, 1997 y 1998): revisar antes de usarlos.
- **Licencia: pendiente de confirmar.** En el sitio del SIGA que se consultó no encontré los términos de uso. Una charla pública de una integrante del INTA dice que la información que genera la institución se comparte con una licencia CC BY-NC (https://yabellini.netlify.app/talk/2022_fosdem), pero **no es la página del SIGA** y no se verificó que aplique a esta serie. Si fuera NC (no comercial), hay que revisar si el uso del proyecto lo respeta. Confirmar con el INTA antes de publicar los datos.

## INA (Instituto Nacional del Agua)

Hay dos informes del propio equipo y **no dicen lo mismo**, por eso se muestran los dos:

| | `docs/datos/ina_lluvia_formosa.md` (17/11/2026) | `docs/fuentes/ina.md` (18/11/2026) |
|---|---|---|
| Interfaz consultada | `https://alerta.ina.gob.ar/pub/datos/` | `https://alerta.ina.gob.ar/a5` |
| Resultado | 10 estaciones de Formosa con series de lluvia registradas, **todas con 0 observaciones** entre 1950 y el 31/10/2026 | 15 estaciones (12 dentro de la provincia y 3 sobre el río Bermejo) con lluvia diaria, de **2019-07-14** a **2026-11-17** |
| Conclusión | «El INA no tiene hoy lluvia diaria de Formosa que podamos usar» | Sí tiene series; **no se descargaron valores** |

**Qué se sabe y qué no.** Las dos consultas usaron interfaces distintas. Coinciden en que las estaciones del INTA que el INA lista no tienen datos propios. La segunda halló series para otras estaciones, pero solo miró el listado y las fechas. **Ninguna descargó ni revisó valores**, así que hoy no se puede decir que el INA sea una fuente usable. Para la demo se usa el SIGA.

- **Corte:** la variable id 1 «precipitación diaria 12Z» corta a las 12 UTC (09:00 de Argentina).
- **Licencia: pendiente.** La página consultada no la indica.
- **Pendiente (del informe del 18/11):** provincia de las 3 estaciones del Bermejo, propietario de cada red, significado de los códigos de disponibilidad (`NRT`, `RT`, `C`, `H`), y bajar y contrastar valores de al menos una estación.
- **Estaciones que parecen ser las mismas del SIGA** (a confirmar): 424 con INA 788, 425 con INA 851 y 51 con INA 1462.

## Red provincial, UPCA y SNIH

**No hay datos cargados ni una fuente verificada de ninguna de las tres.** Esta ficha solo registra su horario de corte (07:00 a 07:00), que viene de las reglas del proyecto. Pendiente para cada una: organismo responsable, enlace a los datos, estaciones, cobertura, licencia o condiciones de uso, y si algún dato del kit del AI LAB las incluye. La lista de las 34 estaciones provinciales tampoco está disponible: `docs/datos/estaciones.csv` (SCRUM-31) usa 34 estaciones **simuladas**, marcadas como tales, hasta tener la oficial (ver `docs/datos/LEEME_estaciones.md`).

## SMN (Servicio Meteorológico Nacional)

- **Qué aporta:** la normal mensual de lluvia 1991-2020 de **Formosa Aero** (WIGOS 0-20000-0-87162), publicada en *Estadísticas Climatológicas Normales 1991-2020* (SMN, 2023, ISSN 2953-5549), https://repositorio.smn.gob.ar/handle/20.500.12160/2506
- **Categoría:** `referencia`. No se suma ni se promedia con lo observado.
- **Licencia:** Creative Commons Reconocimiento 2.5 Argentina, según el repositorio.
- **Limitaciones:** una sola estación, en la ciudad de Formosa. No representa a toda la provincia y no se aplicó a otras estaciones. Los valores se copiaron a mano del PDF (falta re-verificar dos meses). Detalle completo en `docs/fuentes/smn-normales.md`.
- **No se cargaron** observaciones diarias del SMN.

## CHIRPS v3 (estimado)

- **Qué es:** lluvia por satélite combinada con estaciones, grilla de 0,05°, de 1981 a la actualidad (Climate Hazards Center, UC Santa Barbara). Página del producto: https://www.chc.ucsb.edu/data/chirps3
- **Categoría:** `estimado`. Siempre separado de lo medido (regla 2).
- **Estado:** **sin cargar** (SCRUM-43, en manos de Alexia). Los valores en los puntos de las estaciones serían estimaciones, no mediciones.
- **Licencia: hay textos que no coinciden y falta confirmarlo en la página del CHC.** El README del proyecto dice CC BY 4.0. El espejo del producto en el registro de datos abiertos de AWS (hecho por dynamical.org) también indica CC BY 4.0 (https://registry.opendata.aws/dynamical-ucsb-chc-chirps/). En cambio, el catálogo de Google Earth Engine dice que el conjunto está en dominio público (https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHC_CHIRPS_V3_PENTAD). En cualquier caso conviene citar la fuente: DOI de los datos 10.15780/G2JQ0P (2025) y artículo en *Scientific Data*, DOI 10.1038/s41597-026-07096-4.
- **Corte horario:** no verificado.

## Datos provistos en el kit del AI LAB

El README del proyecto los menciona como fuente, pero **no hay una lista de qué archivos son ni de qué organismo vienen**. Pendiente: que el equipo la complete antes de entregar.

## Qué falta para cerrar esta ficha

1. Confirmar la licencia o los términos de uso del SIGA/INTA y del INA.
2. Identificar y documentar la red provincial, UPCA y SNIH (organismo, enlace, licencia, estaciones).
3. Aclarar la discrepancia entre los dos informes del INA bajando y revisando valores reales.
4. Resolver la licencia de CHIRPS en la página del CHC y su corte horario antes de cargarlo.
5. Listar los archivos del kit del AI LAB.
