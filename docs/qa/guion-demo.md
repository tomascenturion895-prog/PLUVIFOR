# Guion de la demo (SCRUM-72)

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Recorrido fijo de unos 5 minutos con **datos reales ya cargados** (3 estaciones del SIGA/INTA, 7.648 días, fecha de corte 31/10/2026). Funciona **sin internet**.

## Antes de empezar (2 minutos)

1. Backend: `cd apps/backend`, activar el entorno y correr `python -m app.cli reset-demo --yes`. Deja la base siempre en el mismo estado.
2. En `.env` poné una clave de práctica en `ADMIN_API_KEY` (hace falta para el paso 6). Después `uvicorn app.main:app`.
3. Frontend: `cd apps/frontend` y `npm run dev`. Abrir <http://localhost:5173>.
4. Si querés que aparezca la referencia del SMN, corré antes `python -m app.cli import-normals`. Suma una cuarta opción, «Formosa Aero (87162)», en la lista de estaciones; el guion no la usa.

**Sin internet:** el mapa pierde las calles de fondo (queda gris) pero se ven el contorno de la provincia, los departamentos y las estaciones. Conviene avisarlo antes de que alguien lo pregunte.

## El recorrido

El período de los pasos 2 a 5 es el mismo: **20/09/2015 al 26/06/2016**. Es el tramo en que la 424 marca 0 mm durante 281 días seguidos y la 425, a 99 km, registra 1.265 mm.

| # | Pantalla | Qué hacer | Qué se tiene que ver | Qué decir |
|---|---|---|---|---|
| 1 | Inicio | Abrir la página. | La pregunta «¿Cuánto llovió, dónde y en qué período?», la frase «nunca como 0 mm» y la leyenda de prototipo abajo. | «Esta herramienta siempre dice qué tan confiable es el dato. Un día sin dato no es 0 mm.» |
| 2 | Mapa | Menú **Mapa**. En Desde y Hasta poner 20/09/2015 y 26/06/2016. | Mapa con el contorno de la provincia y las estaciones; una con círculo grande oscuro (la 425, 100 mm o más). La leyenda aclara «hueco ≠ 0 mm» y que el color no es un total departamental. | «No se pinta de cero lo que no se midió.» |
| 3a | Estación | Menú **Estación**, elegir **El Colorado - EEA El Colorado (424)** y el mismo período. | Acumulado **0 mm**, 281 de 281 días, y la advertencia **«Racha de ceros»** («no se da por buena»), más «Dato sin validar». | «La 424 dice que no llovió en 9 meses. El sistema no lo da por bueno.» |
| 3b | Estación | Cambiar a **Bartolomé de las Casas (425)**. | Acumulado **1.265 mm**, sin la advertencia de racha. | «La vecina, a 99 km, registró 1.265 mm en el mismo tramo.» |
| 4 | Comparador | La pantalla todavía está en construcción: se muestra la API. Abrir <http://localhost:8000/docs>, `GET /api/rainfall/compare`, con `station_ids` = `2,3`, `from` = `2015-09-20` y `to` = `2016-06-26`. | En la 424: `ceros_prolongados` y `inconsistente_con_vecinas`; en la 425: 1265 mm. | «La API compara estaciones y devuelve las advertencias; la pantalla es lo que sigue.» |
| 5 | Parte pluvial | Menú **Parte pluvial**, tildar 424 y 425, mismo período, **Generar parte**. | Texto con fecha de corte 31/10/2026, 0,0 mm contra 1.265,0 mm, el aviso «La estación marca 0 mm, pero la vecina 425 (a 99 km) registró 1265 mm», los eventos intensos de la 425 y «los acumulados de estaciones distintas no se suman entre sí». Botones **Copiar texto** e **Imprimir**. | «Esto se puede copiar o imprimir, con las advertencias adentro.» |
| 6 | Importar | Menú **Importar y auditar**, escribir la clave de práctica, elegir un CSV de lluvia diaria con el formato del SIGA (ejemplo abajo) y **Auditar**. **No** apretar «Confirmar carga». | Informe: 4 filas leídas, 2 aceptadas, 2 rechazadas (milímetros negativos y fecha posterior al corte) y «Todavía no se guardó nada». | «Antes de guardar, el sistema dice qué acepta y qué rechaza y por qué.» |

CSV de ejemplo para el paso 6 (4 filas; una vacía queda como «sin valor», una negativa y una posterior al corte se rechazan):

```csv
estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,categoria,fuente
425,Bartolomé de las Casas - EEA El Colorado,2026-10-01,12.5,,mm,dato,,OBSERVADO,SIGA INTA
425,Bartolomé de las Casas - EEA El Colorado,2026-10-02,,,mm,fila_sin_valor,,OBSERVADO,SIGA INTA
425,Bartolomé de las Casas - EEA El Colorado,2026-10-03,-5,,mm,dato,,OBSERVADO,SIGA INTA
425,Bartolomé de las Casas - EEA El Colorado,2026-11-15,20,,mm,dato,,OBSERVADO,SIGA INTA
```

## Resultado del ensayo (19/11/2026)

Se corrió el guion completo **dos veces seguidas**, cada vez con la base reiniciada (`reset-demo`), con un Chrome de escritorio (1280×900) y **bloqueando todo pedido fuera de la computadora** (15 pedidos externos abortados, que eran el fondo del mapa y similares). En las dos corridas pasaron los 7 pasos (1, 2, 3a, 3b, 4, 5 y 6) y no hubo errores de JavaScript en la página. Cada paso se verificó contra el texto esperado de la tabla.

**Cómo se hizo:** con un script local de Playwright que no está en el repositorio. Verifica el texto de cada pantalla, no la apariencia.

## Lo que no cubre y lo que quedó afuera

- **«Reporte policial»**: la tarea original lo nombra, pero **no existe** en el sistema ni en `AGENTS.md`. No se incluyó. Si el equipo lo necesita, hay que definir qué es.
- **Comparador**: el paso 4 usa la API porque la pantalla está en construcción. Cuando exista, reemplazar ese paso.
- **Ensayo humano:** lo corrió un script, no una persona. Falta que alguien del equipo lo recorra a mano, con el ritmo de la presentación, y anote lo que se atasque (SCRUM-80).
- **Celular real y otros navegadores:** no se probó (ver `docs/qa/auditoria-celular.md`).
- **Qué falló y qué se arregló:** al preparar el ensayo apareció un problema de la guía de instalación (la base vacía daba error 500), corregido en `docs/ENTORNO.md` (SCRUM-74). No hubo otras fallas en el recorrido.
