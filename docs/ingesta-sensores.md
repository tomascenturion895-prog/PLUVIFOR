# Ingesta de sensores (simulados)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

**Estado: contrato definido y probado con un simulador. No hay sensores reales.** Esta pieza deja listo *cómo entrarían* las lecturas de pluviómetros automáticos el día que existan (SCRUM-94). Es candidata a recortar: no toca el núcleo de lluvia.

## Por qué suma a la solución

Responde a «¿cuánto llovió, dónde y en qué período?» con una fuente más en el futuro, sin mezclarla con lo que hoy es confiable. Mientras no haya hardware, lo único que entra es lo que genera el simulador, y siempre rotulado como **simulado**.

## Reglas

1. **Todo entra como `simulado`.** La categoría no viene en el pedido (si un cliente la manda, la API responde 422). Aceptar sensores reales sería una decisión del equipo y una categoría nueva.
2. **Nunca se suma a las series.** Las lecturas viven en su propia tabla (`sensor_readings`); ninguna consulta de lluvia, acumulado, comparador ni parte las lee. Observado, referencia, estimado y simulado van separados.
3. **Un hueco no es 0 mm.** `mm` es obligatorio. Si un dispositivo no pudo medir, no envía nada: no se manda ni `0` ni `null`. Un `0` es una medición («midió y no llovió»).
4. **Corte de datos 31/10/2026.** Se rechaza una lectura cuyo día en Argentina sea posterior.
5. **No se inventan coordenadas.** La ubicación es opcional (`lat` y `lon` juntas); el simulador no la informa.
6. **Autenticación por clave.** Encabezado `X-Device-Key`, comparado con `DEVICE_API_KEY` (variable de entorno, nunca en el código). Sin clave configurada, la ingesta queda cerrada (403); con clave ausente o incorrecta, 401. La clave de administración (`ADMIN_API_KEY`) no sirve acá. En el prototipo hay una sola clave para todos los dispositivos; con hardware real correspondería una por dispositivo.

## Contrato

Está en `apps/api-go/openapi.yaml` (`/api/sensor-readings`). Go reenvía estos pedidos a Python, que es el único que escribe en la base.

`POST /api/sensor-readings`

```json
{ "device_id": "SIM-001", "read_at": "2026-10-20T07:00:00-03:00", "mm": 12.5 }
```

- `device_id`: letras, números, punto, guion y guion bajo (hasta 64).
- `read_at`: fecha y hora **con zona horaria**; se guarda y devuelve en UTC.
- `mm`: entre 0 y 1000; milímetros medidos por el dispositivo.
- Respuestas: `201` guardada; `200` ya estaba cargada con el mismo valor (reenviar no duplica); `409` misma hora con otro valor (no pisa el dato); `401` / `403` clave; `422` datos inválidos.

`GET /api/sensor-readings?device_id=&limit=&offset=` (público): últimas lecturas, con `category: "simulado"` y un `notice` que lo aclara.

## Demo

Con el backend corriendo y `DEVICE_API_KEY` en el `.env` (cualquier texto largo y al azar), desde `apps/backend`:

```bash
alembic upgrade head                 # crea la tabla sensor_readings si falta
python -m simulador --url http://localhost:8000 --dispositivos 3 --dias 7
```

Envía una lectura diaria por dispositivo (07:00 hora de Argentina, hasta el corte) con una semilla fija: el mismo comando genera siempre las mismas lecturas. Algunos días un dispositivo «no reporta»: ese día no hay lectura. Volver a correrlo no duplica nada. La clave sale de `DEVICE_API_KEY`, no de la línea de comandos.

En la interfaz hay una pantalla propia, **Sensores** (`/sensores`): una tarjeta por dispositivo con su última lectura, un gráfico de las lecturas (un día sin lectura es un hueco rayado, nunca 0 mm) y la tabla paginada, todo con la insignia **Simulado**. Las últimas lecturas también se ven en **Salud de la red → Sensores (simulados)**.

`GET /api/sensor-readings/devices` (público) devuelve un resumen por dispositivo: cantidad de lecturas, primera, última y los mm de la última.

Cada dispositivo trae su **estado**, calculado contra la fecha de corte (31/10/2026) y no contra hoy, con la misma regla que la salud de las estaciones: `en_silencio` si su última lectura es de hace más de `silent_after_days` días (30 por defecto, provisional y a confirmar; se puede pedir otro valor de 1 a 365). Un silencio no es 0 mm: el dispositivo sigue mostrando su última lectura real y los días sin lectura son «sin lectura».

## Qué no hace

No valida contra hardware real, no estima huecos con estas lecturas ni las mezcla con las estaciones, y no tiene una clave por dispositivo. Todo eso queda para cuando exista un sensor real y el equipo decida cómo incorporarlo.
