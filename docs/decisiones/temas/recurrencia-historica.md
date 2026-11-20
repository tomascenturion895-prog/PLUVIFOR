# Recurrencia histórica de lluvia intensa

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Nota de fundamento según `AGENTS.md`: es el tramo de «predicción» que los datos actuales permiten sostener. Decisión del 20/11/2026 (de palabra; falta confirmarla por escrito). Todavía **no hay tarea de Jira**.

## Qué es

Cuántas veces una estación registró 50 mm o más (y 100 mm o más) en un día, y cada cuánto lo hizo **en promedio durante el período observado**. Se ve en la pantalla de cada estación («Recurrencia histórica de lluvia intensa») y sale de `GET /api/recurrence`.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Pone en contexto un día intenso: no solo «llovió 112 mm», sino «un día así ocurrió N veces en 6,6 años de datos válidos de esta estación». Ayuda a decidir mejor con el dato que ya se muestra.

## Por qué no es un pronóstico

Es una **frecuencia pasada**. «Una vez cada 6,6 años» describe lo que pasó, no cuándo va a volver a pasar: la lluvia no tiene un reloj, y menos todavía con El Niño 2026/27. El texto de la interfaz y de la API lo dice. No hay ningún modelo que mire hacia adelante.

## Reglas

1. **Solo la serie `observado`.** Nada simulado, estimado ni de referencia entra en el conteo.
2. **Un hueco no es 0 mm.** Un día `sin_fila` o `fila_sin_valor` no cuenta como lluvia ni como día seco, y no suma al período observado.
3. **Se excluyen los días con dato dentro de una racha de ceros prolongados** (advertencia de 60 días o más): pueden ser un sensor sin registrar, y contarlos haría parecer que llueve menos de lo real.
4. **Historia mínima de 5 años de dato válido.** Con menos, se informa cuántas veces ocurrió pero **no se calcula ninguna frecuencia**. Con 0 eventos tampoco se inventa un intervalo. El umbral de 5 años es provisional, a confirmar con el equipo.
5. **Nada posterior al corte** (31/10/2026).
6. **Los umbrales** (50 y 100 mm por día) son los mismos de `GET /api/events`.

## Qué muestran hoy los datos reales (SIGA/INTA, 2013–2023)

| Estación | Años válidos | Días ≥ 50 mm | Días ≥ 100 mm | Frecuencia |
|---|---|---|---|---|
| 51 · El Colorado (EMC) | 2,4 | 18 | 2 | No se calcula (historia insuficiente) |
| 424 · El Colorado (EEA) | 6,6 | 30 | 1 | Sí, con 281 días de ceros excluidos |
| 425 · Bartolomé de las Casas | 4,6 | 27 | 4 | No se calcula (historia insuficiente) |

Dos de las tres estaciones no llegan a 5 años: el sistema lo dice en lugar de mostrar un número que parezca más firme de lo que es. Cargar el INA y CHIRPS ampliaría la historia; hoy ninguno de los dos está cargado.

## Qué no incluye

- **Pronóstico de lluvia** ni modelo de ningún tipo. Con tres estaciones, una con un cero prolongado, no hay base para uno.
- **Períodos de retorno estadísticos** (Gumbel, GEV) ni extrapolación a lluvias más grandes que las observadas: harían falta series más largas y validadas.
- **Zonas inundables ni evacuaciones.** Siguen fuera hasta que haya relieve y datos oficiales (ver `avisos-a-la-poblacion.md`).
- **Una alerta.** No avisa nada a nadie.

## Qué falta decidir al equipo

- Si el mínimo de 5 años de dato válido es el correcto.
- Si se carga el histórico del INA y CHIRPS (licencia del INA pendiente de confirmar) para ampliar la historia.
