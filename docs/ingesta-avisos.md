# Avisos a la población (canal simulado)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

**Estado: suscripción, confirmación, baja y armado del aviso, todo probado. No se envía ningún mensaje real.** Los mensajes quedan en una bandeja rotulada como **simulada**. La nota de fundamento, con lo que incluye y lo que no, está en [`docs/decisiones/temas/avisos-a-la-poblacion.md`](decisiones/temas/avisos-a-la-poblacion.md).

## Cómo funciona

1. **Suscripción.** La persona deja su teléfono (y, si quiere, una estación). Se le «manda» un código de 6 dígitos que vence a los 15 minutos. Hoy el código queda en la bandeja simulada; la respuesta de la API nunca lo trae.
2. **Confirmación.** Con el código queda confirmada. Tras 5 intentos fallidos hay que pedir otro (429). Sin confirmar, no recibe nada.
3. **Baja.** Cuando pide la baja no recibe más avisos. La respuesta es igual exista o no el número.
4. **Aviso.** Una persona del equipo, con la clave de administración, mira la vista previa de una estación y un día y, si corresponde, lo pone en la bandeja de las suscripciones confirmadas.

## Reglas

- **Solo un día observado con dato y 50 mm o más genera un aviso** (100 mm o más se rotula como nivel 100). Un hueco (`sin_fila` o `fila_sin_valor`) responde `sin_dato`: no avisa y nunca se cuenta como 0 mm.
- Una lectura de sensor simulada, una estimación o una referencia climática no generan avisos: la vista previa lee solo la serie `observado`.
- No se avisa sobre un día posterior al corte de datos (31/10/2026).
- El mensaje dice la estación, el valor, la fecha, que es dato observado y si está sin validar. **No ordena ni recomienda evacuar**: remite a Defensa Civil. Lleva la leyenda de prototipo.
- Del teléfono se guarda un resumen (HMAC-SHA256 con `ALERTS_SECRET`) y los últimos 4 dígitos. Sin `ALERTS_SECRET`, las suscripciones quedan cerradas (403).
- Solo el personal, con `X-API-Key`, ve la vista previa, manda el aviso y lee la bandeja.

## Contrato

Está en `apps/api-go/openapi.yaml` (`/api/alerts/*`). Go reenvía estos pedidos a Python, que es el único que escribe en la base.

| Ruta | Quién | Para qué |
|---|---|---|
| `POST /api/alerts/subscriptions` | público | pedir avisos `{phone, station_id?}` → 202 |
| `POST /api/alerts/subscriptions/confirm` | público | `{phone, code}` → 200, 422 o 429 |
| `POST /api/alerts/subscriptions/unsubscribe` | público | `{phone}` → 200 |
| `GET /api/alerts/preview?station_id=&date=` | personal | ver qué avisaría el sistema |
| `POST /api/alerts/send?station_id=&date=` | personal | poner el aviso en la bandeja simulada |
| `GET /api/alerts/outbox` | personal | ver lo que se enviaría |

## Demo

En el `.env`: `ALERTS_SECRET` (texto largo y al azar) y `ADMIN_API_KEY`. Desde `apps/backend`:

```bash
alembic upgrade head          # crea las tablas de avisos
uvicorn app.main:app --reload
```

En la interfaz: **Avisos** (`/avisos`) para suscribirse, confirmar y darse de baja. Con la clave de administración, la misma pantalla muestra la bandeja simulada, que es donde se lee el código.

## Qué no hace (pendiente)

- **No envía por WhatsApp ni por ningún canal real.** Haría falta una cuenta de empresa verificada, un número dedicado, plantillas aprobadas por Meta y confirmar el costo.
- **No guarda el número completo**, así que no podría enviar de verdad todavía: falta cifrarlo y decidir quién lo custodia.
- **La baja por «BAJA» desde el mismo chat** requiere el canal real; hoy se hace desde la pantalla, y cualquiera que conozca un número podría darlo de baja. Con el canal real, la baja la haría el dueño del número respondiendo desde su teléfono.
- **No hay predicción, zonas inundables ni evacuaciones**, y no hay cuentas del personal con inicio de sesión (hoy es la clave de administración).
