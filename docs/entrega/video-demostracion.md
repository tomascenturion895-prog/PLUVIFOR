# Video de demostración (SCRUM-76)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Registro de entrega del video de demostración del prototipo **PLUVIFOR** (Pluviometría Integrada de Formosa), desarrollado por el Equipo 5 «SpaidyCode» para el Desafío 2 · Reporte pluvial de la *Operación Agua* (AI LAB «Misión: Código Formosa», El Niño 2026/27).

---

## 1. Enlace al video

- **Enlace:** `[AQUÍ_VA_EL_ENLACE_AL_VIDEO_SUBIDO]`
- **Duración:** 120 segundos (02:00 máximo).
- **Subtítulos:** Español (diseñado para comprenderse completamente sin audio).
- **Resolución sugerida:** 1080p (1920×1080) a 30/60 fps.

---

## 2. Preparación previa para la grabación

Antes de iniciar la grabación:

1. **Reiniciar la base con datos limpios de demo:**
   ```bash
   cd apps/backend
   python -m app.cli reset-demo --yes
   ```
2. **Levantar los servicios:**
   - **Terminal 1 (Backend):**
     ```bash
     cd apps/backend
     uvicorn app.main:app --reload
     ```
   - **Terminal 2 (Frontend):**
     ```bash
     cd apps/frontend
     npm run dev
     ```
3. **Navegador:**
   - Abrir `http://localhost:5173` en pantalla completa o ventana limpia a 1920×1080.
   - Período clave de demostración: **20/09/2015 al 26/06/2016** (tramo donde la estación 424 marca 0 mm en 281 días seguidos mientras la 425 registra 1.265 mm).

---

## 3. Guion y cronograma segundo a segundo (00:00 a 02:00)

| Tiempo | Pantalla / Sección | Acción en pantalla | Subtítulo / Texto en pantalla | Idea clave a transmitir |
|---|---|---|---|---|
| **00:00 - 00:15** (15 s) | **Inicio** (`/`) | Mostrar pantalla inicial, leyenda de prototipo y accesos rápidos. | *«PLUVIFOR: reporte pluvial provincial con rigor en la calidad del dato. Un hueco de medición nunca es 0 mm.»* | Presentar el problema y la regla de oro: sin dato ≠ cero. |
| **00:15 - 00:35** (20 s) | **Mapa Provincial** (`/map`) | Navegar a Mapa. Ingresar período `20/09/2015` a `26/06/2016`. Mostrar círculos de estaciones y capas. | *«Visualización geográfica por departamentos. Los días sin datos no se rellenan artificialmente.»* | Mapa interactivo provincial y advertencia de cobertura. |
| **00:35 - 01:00** (25 s) | **Estación** (`/stations`) | Seleccionar estación 424 (El Colorado). Mostrar 0 mm y advertencia «Racha de ceros». Luego cambiar a 425 (Bartolomé de las Casas) con 1.265 mm. | *«Caso real: Estación 424 reporta 0 mm por 281 días seguidos. El sistema detecta anomalía mientras la vecina (425) registró 1.265 mm.»* | Advertencias de calidad en acción: ceros prolongados no se dan por buenos. |
| **01:00 - 01:20** (20 s) | **Comparador** (`/compare`) | Seleccionar estaciones 424 y 425 en el mismo período. Mostrar banderas de inconsistencia con vecinas. | *«Comparación directa entre redes: advertencias automáticas ante disparidad de horarios de corte o lecturas dudosas.»* | Comparabilidad honesta entre redes y fuentes. |
| **01:20 - 01:40** (20 s) | **Parte Pluvial** (`/report`) | Generar parte pluvial para las estaciones. Mostrar resumen, notas de calidad y botones «Copiar» e «Imprimir». | *«Parte pluvial consolidado para toma de decisiones y defensa civil. Integra advertencias sin mezclar observado con estimado.»* | Generación de reportes listos para imprimir o compartir. |
| **01:40 - 02:00** (20 s) | **Importación y auditoría** (`/import`) | Mostrar pantalla de importación, carga de CSV de prueba y auditoría fila por fila con rechazos explicados. | *«Ingesta segura y auditable: cada fila se valida. Las anomalías o datos post-corte (31/10/2026) se rechazan con motivo antes de guardar.»* | Trazabilidad y auditoría estricta de cada dato ingresado. |

---

## 4. Criterios de aceptación (Definition of Done)

- [x] Guion estructurado según el recorrido de prueba de SCRUM-72.
- [x] Duración estricta de 120 segundos o menos.
- [x] Contenido subtitulado en español comprensible sin pista de audio.
- [x] Respeta las reglas de integridad: corte al 31/10/2026, un hueco no es cero, fuentes y categorías separadas.
- [ ] Enlace del video renderizado y subido incorporado en este documento.

