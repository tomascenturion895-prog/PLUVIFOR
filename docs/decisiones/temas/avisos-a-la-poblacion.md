# Avisos a la población (cuentas, suscripción y mensajería)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Nota de fundamento según `AGENTS.md`: tema fuera del núcleo de lluvia. Decisión del equipo del 20/11/2026 (de palabra; falta confirmarla por escrito). Todavía **no hay tarea de Jira**.

## Qué es

Que una persona pueda **suscribirse** para recibir por mensajería (WhatsApp, por ser el canal más usado) un aviso **informativo** cuando la lluvia observada pasa un umbral que el sistema ya calcula (≥50 y ≥100 mm en el día, `GET /api/events`). Incluye cuentas para el **personal** que revisa y envía los avisos.

## Cómo ayuda a responder ¿cuánto llovió, dónde y en qué período?

Lleva la respuesta a quien la necesita sin que tenga que abrir la aplicación: «en tu zona llovió tanto, medido por tal estación, en tal fecha». Cada aviso dice la fuente, la categoría y la advertencia de calidad que hoy se ve en pantalla.

## Reglas (valen igual que en el resto del sistema)

1. **Un aviso nunca dice 0 mm cuando falta el dato.** Sin dato, no se avisa nada; no se rellena.
2. **Solo lo observado dispara un aviso.** Una lectura simulada, una estimación o una referencia climática **nunca** envía un mensaje real.
3. **Cada mensaje lleva fuente, categoría, fecha y «sin validar»** si corresponde, y la leyenda de prototipo. No ordena ni recomienda evacuar: remite a Defensa Civil.
4. **Una persona del equipo revisa y confirma cada aviso** antes de que salga. No hay envío automático.
5. **Doble confirmación.** Quien se suscribe confirma con un código de un solo uso; sin confirmar, no recibe nada. Se puede dar de baja con una palabra («BAJA») y la baja se respeta siempre.
6. **Datos personales mínimos.** Del teléfono se guarda un resumen irreversible (HMAC con una clave del entorno) y los últimos dígitos para mostrar. Guardar el número completo para enviar de verdad queda **pendiente**: hace falta cifrarlo y decidir quién lo custodia (Ley 25.326).
7. **Los secretos van en `.env`**, nunca en el código ni en un commit.

## Qué incluye hoy (prototipo)

- Suscripción con código de confirmación y baja.
- Un **canal simulado**: los avisos quedan registrados como «mensaje que se enviaría», rotulados como simulados. No se envía nada a nadie.
- Una vista previa del aviso que se generaría para un evento intenso, con su texto completo, para que el personal la revise.

## Qué no incluye (y por qué)

- **Envío real por WhatsApp.** Requiere una cuenta de empresa verificada, un número dedicado, plantillas aprobadas por Meta y un costo por conversación que hay que confirmar. Se haría con la WhatsApp Business Platform (Cloud API); los bots que usan WhatsApp Web violan sus términos y no se usan.
- **Predicción y zonas inundables.** No existe ningún modelo ni capa de inundación, y no se inventan. Entrarían solo con una capa oficial o validada (Defensa Civil, INA, municipio) con licencia confirmada, y con el error del modelo medido, siempre como `estimado`.
- **Órdenes de evacuación.** Las dicta Defensa Civil. Un aviso falso o tardío tiene un costo real; este sistema es un prototipo y se declara «no es una herramienta oficial».
- **Cuentas del personal con inicio de sesión.** Hoy la escritura se protege con claves de API (administración y dispositivos). Reemplazarlas por cuentas con roles es la siguiente etapa y toca todas las rutas que escriben: se hace en su propio PR, con revisión.

## Qué falta decidir al equipo

- Con quién se coordina un canal real (Defensa Civil u otra área) y quién responde por cada aviso.
- Qué teléfono y qué cuenta de empresa se usarían, y quién paga la mensajería.
- Cómo se resguarda el número de teléfono completo.
- Si los umbrales de 50 y 100 mm son los correctos para avisar a la población (hoy son los de los eventos descriptivos).

## Dónde está

docs/ingesta-avisos.md
