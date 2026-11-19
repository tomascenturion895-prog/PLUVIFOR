# CHIRPS v3 · Extracción de lluvia diaria estimada en puntos de estaciones

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

## 1. Identificación y origen

- **Producto:** Climate Hazards Center Infrared Precipitation with Stations (CHIRPS v3).
- **Institución:** Climate Hazards Center (CHC), University of California, Santa Barbara (UCSB).
- **Página oficial:** https://www.chc.ucsb.edu/data/chirps3
- **Resolución espacial:** Grilla casi-global de 0,05° (~5,3 km).
- **Cobertura temporal:** 1981 a la actualidad.
- **Categoría en PLUVIFOR:** `estimado` (Regla 2: nunca se mezcla, suma ni promedia con lluvia `observada`).
- **Cita y DOI:**
  - Repositorio de datos: https://doi.org/10.15780/G2JQ0P (2025).
  - Publicación científica: *Scientific Data*, DOI: [10.1038/s41597-026-07096-4](https://doi.org/10.1038/s41597-026-07096-4).

## 2. Verificación de Licencia

En la página oficial de CHIRPS v3 (`https://www.chc.ucsb.edu/data/chirps3`), en la sección *Data Citation*, se establece:
> *"CHIRPS3 is in the public domain, as registered with Creative Commons, and is licensed under a Creative Commons Attribution 4.0 International License (CC BY 4.0)."*

Por ende, el producto es compatible con el uso bajo atribución (CC BY 4.0).

## 3. Estado de Descarga y Acceso a la Fuente

1. **Intento de descarga directa:**
   Los endpoints HTTP y directorios de descargas públicas de CHIRPS v3 (`https://data.chc.ucsb.edu/products/CHIRPS/v3.0/...`) arrojan `HTTP 403: Forbidden` ante peticiones automáticas estándar o requieren cliente FTP/autenticación de red institucional.
2. **Regla de integridad (AGENTS.md):**
   * *«No inventes nada: ni datos, ni coordenadas, ni endpoints, ni dependencias.»*
   * *«Para tu IA: Si no podés descargar los datos, dejá la tarea documentada y avisá. No generes valores.»*
   En consecuencia, **no se generan datos sintéticos ni ficticios**.
3. **Mecanismo de extracción en una máquina con acceso:**
   Para extraer CHIRPS v3 en las coordenadas de las estaciones verificadas de Formosa (por ejemplo, vía Google Earth Engine `UCSB-CHC/CHIRPS_V3_DAILY_RNL` o leyendo los archivos NetCDF/GeoTIFF globales de 0,05° con `xarray`/`rasterio`), se debe generar el archivo CSV con la siguiente estructura requerida por el conector `chirps_v3`:

```csv
estacion_id,fecha,mm,unidad,estado,categoria,fuente
424,2016-01-01,12.4,mm,dato,estimado,CHIRPS v3
424,2016-01-02,,mm,sin_fila,estimado,CHIRPS v3
```

## 4. Conector e Ingesta en Backend

Se implementó el conector `ChirpsCsvConnector` en `apps/backend/app/ingestion/chirps.py` registrado bajo la fuente `chirps_v3`:
- Categoría fija: `estimado`.
- Valida que `mm` sea nulo en caso de hueco (`sin_fila` o `fila_sin_valor`) y positivo en caso de `dato`.
- Los datos se cargan vinculados a las estaciones del sistema y se auditan en `import_logs`.
- Los acumulados y series se mantienen rigurosamente independientes de las observaciones (`observado`), activando la advertencia `observado_vs_estimado` si se intentan comparar.
