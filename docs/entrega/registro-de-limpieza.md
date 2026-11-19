# Registro de limpieza

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Tarea SCRUM-58. Cada decisión sobre los datos: qué se hizo, con qué fuente, por qué y cuántas filas afectó. Se redactó leyendo el código de `apps/backend/app/` tal como está en la rama `qa` el 19/11/2026 y `docs/datos/LEEME_siga.md`. **Solo figura lo que el código o el LEEME dicen que se hizo.**

**Sobre las fechas.** Las decisiones que se tomaron al preparar el CSV llevan la fecha del LEEME (consulta del SIGA el 16/11/2026, originales bajados el 18/11/2026). Las que aplica el código en cada carga no tienen fecha propia: valen desde la versión del código citada, y cada carga queda con su fecha y hora en `import_logs`.

## 1. Qué datos hay cargados

| Fuente | Categoría | Qué se cargó | Transformaciones |
|---|---|---|---|
| SIGA / INTA | `observado` | 3 estaciones y 7.648 filas de lluvia diaria (`docs/datos/`) | Las de las secciones 2 y 3 |
| SMN | `referencia` | Normal mensual 1991-2020 de Formosa Aero (12 valores) | Copiada a mano de la publicación; ver `docs/fuentes/smn-normales.md` |
| INA, red provincial, UPCA, SNIH, CHIRPS | | **Nada.** No hay datos cargados de estas fuentes | Ninguna |

## 2. Del SIGA al CSV (antes de entrar al sistema)

Fuente: `docs/datos/LEEME_siga.md`. El CSV (`lluvia_diaria_siga_formosa.csv`) se armó a partir de las respuestas originales del SIGA, guardadas sin modificar en `docs/datos/original/` (41 archivos, con `indice_descarga.json`, que lista las filas de cada pedido).

| # | Fecha | Decisión | Motivo | Filas |
|---|---|---|---|---|
| L1 | 16-18/11/2026 | Se pidió al SIGA en ventanas de dos años | El servidor corta en 1.000 filas por pedido | Todas |
| L2 | 16-18/11/2026 | Se armó el calendario completo de cada estación; los días que el SIGA no devuelve se agregaron como `sin_fila` | Que los huecos queden a la vista | 2.018 días `sin_fila` |
| L3 | 16-18/11/2026 | Los valores vacíos se dejaron vacíos y se marcaron `fila_sin_valor` | Un día sin registro no es un día sin lluvia | 365 días `fila_sin_valor` |
| L4 | 16-18/11/2026 | Se redondeó a 2 decimales | El SIGA trae hasta 6 decimales en algunas filas | Pocas (el LEEME no da la cifra); 2 diferencias de redondeo en la 424 contra el original: 9,8 contra 9,800001 y 44,6 contra 44,59998 |
| L5 | 16-18/11/2026 | No se corrigió ni se completó ningún valor | Regla del kit | 0 |
| L6 | 16-18/11/2026 | De la estación 51 solo se incluyó desde 2013 (909 filas) | Recorte del tramo útil; la serie completa (20.268 filas desde 1960) se baja con `descargar_siga.py` | 909 de 20.268 |
| L7 | 16-18/11/2026 | Se agregó la columna `bandera` con `ceros_prolongados` para tramos de 60 días o más con 0 mm | Advertir ceros no creíbles | 281 días (estación 424) |

El valor de lluvia del CSV (`mm_pluviometrica`) es el campo `precDiaPlub` del SIGA. La columna `mm_cronologica` (`precDiaCrono`, solo estaciones automáticas) se conserva sin tocar.

**Lo que no se pudo comprobar contra el código:** el programa que armó el CSV a partir de los originales **no está en el repositorio** (`descargar_siga.py` solo descarga los originales). El LEEME informa que se compararon los valores `dato` del CSV con `precDiaPlub` de los originales: coinciden salvo los dos redondeos de L4.

## 3. Al entrar al sistema (lo que hace el código en cada carga)

Archivos: `app/ingestion/upload.py`, `siga.py`, `stations.py`, `validation.py`, `types.py`; `app/services/importer.py`; `app/repositories/ingestion.py`.

### 3.1 Control del archivo

| # | Decisión | Motivo | Respuesta |
|---|---|---|---|
| C1 | Solo se acepta un nombre terminado en `.csv` | No procesar otros formatos | 422 `invalid_file` |
| C2 | Se rechaza un archivo vacío | | 422 |
| C3 | Se rechaza un archivo de más de 5 MB (`MAX_UPLOAD_BYTES`) | Entrada no confiable | 413 |
| C4 | Se rechaza un archivo con un byte nulo o con la firma de un formato binario (zip, pdf, exe, imágenes, gzip, SQLite, etc.) | Que un binario no pase por CSV | 422 |
| C5 | Se rechaza un archivo al que le faltan columnas obligatorias (`estacion_id`, `fecha`, `mm_pluviometrica`, `mm_cronologica`, `unidad`, `estado`, `categoria`) | No adivinar columnas | 422 |

### 3.2 Control de cada fila de lluvia

Cada fila se acepta o se rechaza con **un motivo**. Nada se descarta en silencio. El orden de las comprobaciones es el de esta tabla.

| # | Motivo de rechazo | Cuándo |
|---|---|---|
| F1 | `estacion_inexistente` | La estación no está en el catálogo de esa fuente |
| F2 | `fecha_invalida` | La fecha no es una fecha ISO válida (por ejemplo `2016-02-30`) |
| F3 | `fecha_posterior_al_corte` | La fecha es posterior al **31/10/2026** (fecha de corte) |
| F4 | `unidad_invalida` | La unidad no es `mm` |
| F5 | `categoria_invalida` | La categoría no es una de las válidas (`observado`, `referencia`, `estimado`) |
| F6 | `estado_invalido` | El estado no es `dato`, `sin_fila` ni `fila_sin_valor` |
| F7 | `mm_invalido` | El valor no es un número finito (texto, `nan`, infinito) |
| F8 | `mm_negativo` | La lluvia es menor que 0 |
| F9 | `estado_incoherente` | Hay valor y el estado no es `dato`, o el estado es `dato` y no hay valor |
| F10 | `duplicado_en_archivo` | Repite estación, fecha y categoría dentro del mismo archivo (queda la primera) |

Reglas de interpretación: un valor **vacío** se guarda como «sin valor» (nulo), **nunca como 0**; un `0` informado se guarda como 0 con estado `dato`. Todo dato entra con `validation = sin_validar` (nadie validó los datos todavía; de ahí la advertencia `dato_sin_validar`).

### 3.3 Control de cada fila del catálogo de estaciones

| # | Motivo de rechazo | Cuándo |
|---|---|---|
| E1 | `texto_con_formula` | Una de las columnas de texto empieza con `=`, `+`, `-`, `@`, tabulación o retorno (inyección de fórmulas en planillas) |
| E2 | `codigo_vacio` | Falta el código o el nombre |
| E3 | `coordenadas_invalidas` | La latitud, la longitud, la altura o las fechas no son números/fechas, falta una de las dos coordenadas, o están fuera de rango |

Las coordenadas no se adivinan: si faltan, quedan vacías y la estación queda con coordenadas `pendiente`.

### 3.4 Guardado

| # | Decisión | Motivo | Efecto |
|---|---|---|---|
| G1 | Una carga confirmada es atómica: si algo falla no se guarda nada | No dejar datos a medias | |
| G2 | La clave de una fila es estación + fecha + categoría. Si ya existe, **se reemplaza** (estado, valor, valor cronológico y validación) | Que repetir una carga no duplique | La cuenta de la carga informa filas nuevas y actualizadas |
| G3 | Una auditoría (no confirmada) por la API no guarda nada ni deja registro | Poder revisar sin tocar | |
| G4 | Después de confirmar lluvia se recalculan las banderas de calidad | Que la advertencia de ceros no quede vieja | Ver la sección 3.5 |

### 3.5 Ceros prolongados

`app/domain/quality.py`. Un tramo de **60 o más días corridos con `dato` igual a 0** queda marcado `ceros_prolongados` (versión de regla `ceros_prolongados/1`, con `min_days = 60`). **Un hueco (`sin_fila` o `fila_sin_valor`) corta el tramo**: no se puede afirmar que no llovió un día del que no hay dato. Las banderas se recalculan completas por estación (se reemplazan las anteriores). El importador **no lee** la columna `bandera` del CSV: la bandera se calcula de nuevo desde los datos. Resultado con el SIGA cargado: un tramo, en la estación 424, del 20/09/2015 al 26/06/2016 (281 días); el dato no se modifica, solo se advierte.

## 4. Huecos reales y ceros reales

| Qué es | Estado | Valor | Cómo se muestra | Se suma |
|---|---|---|---|---|
| Hay medición y fue 0 | `dato` | 0 | 0 mm | Sí |
| Hay medición | `dato` | n | n mm | Sí |
| El día existe en la fuente pero sin valor | `fila_sin_valor` | nulo | «sin dato» | **No** |
| El día no existe en la fuente | `sin_fila` | nulo | «sin dato» | **No** |

Un período sin ningún día con dato da acumulado «sin dato» (nulo), no 0. Con el SIGA cargado: 5.265 `dato`, 365 `fila_sin_valor` y 2.018 `sin_fila` (7.648 filas leídas, 0 rechazadas).

## 5. Qué se descartó, qué se corrigió

- **Corregido: nada.** Ningún valor se corrigió ni se completó.
- **Descartado:** de los datos reales del SIGA, **0 filas**. Las filas que no cumplan los motivos F1 a F10 o E1 a E3 se rechazan y quedan contadas por motivo.
- **Fuera de la carga por decisión de alcance:** lo posterior al 31/10/2026 (los datos del SIGA terminan antes: 28/06/2015, 07/12/2022 y 24/03/2023).

## 6. Trazabilidad

- **`import_logs`** (una fila por carga confirmada): fuente, modo, estado, nombre del archivo, **SHA-256**, filas leídas, aceptadas y rechazadas, rechazos agrupados por motivo (JSON), fecha de corte aplicada y fecha y hora de inicio. Se consulta con `GET /api/import/logs`.
- **Originales:** `docs/datos/original/` (respuestas del SIGA sin modificar) y `docs/datos/descargar_siga.py` para repetir la descarga. El LEEME informa que `siga_diario_425_2019_2020.json` está vacío: el SIGA no devolvió filas para esa estación en 2019 y 2020 (hueco de la fuente, no ceros).
- **Cada fila de lluvia** guarda el `import_id` de la última carga que la escribió.

## 7. Lo que hay que saber (diferencias y límites)

1. **«Coordenadas verificadas» significa «tiene coordenadas».** El código marca una estación como `verificada` cuando trae latitud y longitud, sin comprobar de dónde salieron. No equivale a una verificación hecha por una persona. Es un riesgo de lectura para la ficha técnica y para el mapa.
2. **Reemplazo por clave (G2).** Si se vuelve a importar una fecha que ya tenía un valor con una fila sin valor, el hueco reemplaza al valor. Es lo que hace hoy el código; no hay una protección que impida pisar un dato con un hueco.
3. **El paso de los originales al CSV no está en el repositorio** (sección 2).
4. **La normal del SMN** entra por `python -m app.cli import-normals`, con sus propios controles (mes de 1 a 12, valor numérico no negativo, período y fuente obligatorios, sin meses repetidos). No pasa por los controles de lluvia diaria. Ver `docs/fuentes/smn-normales.md`.
5. La API usa solo `mm_pluviometrica`; `mm_cronologica` se guarda pero no se muestra.
6. No hay fuente cargada para la red provincial, UPCA, SNIH, INA ni CHIRPS: no hay nada que limpiar de ellas todavía.
