# API del INA: ¿hay lluvia diaria de estaciones de Formosa?

PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Tarea: SCRUM-27 · Consultado: 17/11/2026 · Fuente: API de datos hidrológicos del INA
(`https://alerta.ina.gob.ar/pub/datos/`, documentada en
<https://www.argentina.gob.ar/ina/recursos/aplicacionweb-datos-hidrologicos>)

## Conclusión

**El INA no tiene hoy lluvia diaria de estaciones de Formosa que podamos usar.**

- Hay 21 estaciones de Formosa en el catálogo del INA (`/estaciones`, filtro `distrito=Formosa`).
- Solo 10 tienen alguna variable de precipitación registrada, y **todas devolvieron 0 observaciones** entre 1950-01-01 y la fecha de corte (31/10/2026).
- Las otras 11 son estaciones hidrológicas (alturas y caudales de ríos). Quedan fuera del alcance de este desafío.

La consulta a la API no reemplaza al SIGA: para la demo seguimos con el SIGA/INTA.

## Estaciones con series de lluvia registradas (todas vacías)

| siteCode INA | Estación | Red | Series de lluvia (varId) | Observaciones |
|---|---|---|---|---|
| 788 | El Colorado - EEA INTA | INTA | 1, 27, 31, 34 | 0 |
| 851 | Bartolomé de las Casas - EEA Colorado | INTA | 1, 27, 31, 34 | 0 |
| 1387 | Comandante Fontana | INTA | 1, 27, 31, 34 | 0 |
| 1436 | Ing. Juárez - EEA Ing. Juárez | INTA | 1, 27, 31, 34 | 0 |
| 1462 | INTA - El Colorado (EMC) | INTA | 1, 27, 31, 34 | 0 |
| 1482 | INTA - Naineck | INTA | 1, 27, 31, 34 | 0 |
| 1522 | Laguna Yema (DAVIS) | INTA | 1, 27, 31, 34 | 0 |
| 1566 | Palo Santo - ICyA CIRN | INTA | 1, 27, 31, 34 | 0 |
| 1601 | San Francisco de Laishi | INTA | 1, 27, 31, 34 | 0 |
| 1766 | Puerto Lavalle | Otras redes hidrológicas | 34 | 0 |

Variables: `1` precipitación diaria 12Z (mm por día), `27` a intervalo nativo, `31` horaria,
`34` de 3 horas. El catálogo de series (`/series`) no informa fechas de inicio y fin
(`from_date`, `to_date` y `obs_count` vienen vacíos), por eso el período se comprobó pidiendo
los datos (`/datos`) de cada serie.

## Estaciones hidrológicas (fuera de alcance)

Puerto Pilcomayo, Bouvier, Puerto Formosa, Bermejo (Prefectura Nacional); Paraguay - Puerto
Formosa, Pilagá - Rn N° 11, Paraguay - La Herradura, Bermejo - Puerto Velaz, Pilcomayo - Puesto
Jerez, El Colorado y Pilcomayo - Puerto Pilcomayo (Red Hidrológica Nacional). Miden altura y
caudal, no lluvia.

## Coincidencias con el SIGA

Tres estaciones del INA parecen ser las mismas del SIGA, por nombre y coordenadas (a confirmar):

| SIGA | INA |
|---|---|
| 424 El Colorado - EEA El Colorado | 788 |
| 425 Bartolomé de las Casas - EEA El Colorado | 851 |
| 51 INTA - El Colorado (EMC) | 1462 |

Si el INA llegara a cargar datos, esas series serían la misma estación en otra fuente, no una
estación nueva (ver `docs/modelo-datos.md`, sección 8, punto 3).

## Cómo se repite la consulta

Todos los pedidos son GET, sin autenticación, a `https://alerta.ina.gob.ar/pub/datos/`:

```
estaciones&distrito=Formosa&format=json
series&format=json
datos&seriesId=<id>&timeStart=1950-01-01&timeEnd=2026-10-31&format=csv
```

Una respuesta con solo el encabezado (`###`) y sin filas significa que la serie no tiene datos.
La respuesta en JSON de una serie vacía es un mensaje de error («No se encontraron resultados»).

## Pendiente

- Preguntar al INA o a la mentoría si las series de las estaciones INTA se van a cargar y desde cuándo (se puede sumar a las preguntas de SCRUM-28).
