# Guion de la demostración de avisos

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Para mostrar en 2 a 3 minutos cómo una persona recibiría los avisos de lluvia. **Todo es simulado**: no se envía nada a WhatsApp ni a ninguna casilla de correo. Conviene decirlo en voz alta al empezar: lo que se vende es la idea y la forma de hacerlo bien, no un envío real.

## Antes de presentar

1. En el `.env`: `ADMIN_API_KEY`, `ALERTS_SECRET` (cualquier texto largo y al azar) y **`ALERTS_DEMO=true`**.
2. Desde `apps/backend`: `alembic upgrade head` y `uvicorn app.main:app --reload`.
3. Desde `apps/frontend`: `npm run dev`. Abrir `http://localhost:5173/avisos`.
4. Tener a mano la clave de administración (la pide el panel del personal).

## Paso a paso

1. **Registro (30 s).** Escribir un teléfono (`+54 370 4123456`) y un correo, elegir una estación o dejar «Todas», y pedir el código. A la derecha aparece el **celular**: llegó el código por WhatsApp. Más abajo, el **correo** de registro.
2. **Confirmación (15 s).** Escribir el código que se ve en el celular y confirmar. Llega la bienvenida por WhatsApp y una notificación en la campana del sistema.
3. **El aviso (60 s).** Abrir «Panel del personal», poner la clave y tocar **«Usar el día de ejemplo»** (estación 424, 10/04/2014, 138 mm: un día real de la serie del SIGA/INTA). Mostrar la **vista previa**: lo revisa una persona antes de que salga. Tocar **«Enviar aviso (simulado)»**.
4. **Lo que se ve (30 s).** En pocos segundos llega el aviso al celular, al correo y a la campana, con un aviso emergente. El texto dice la estación, el valor, la fecha, que es dato **observado** y **sin validar**, y que **no es una orden de evacuar**.
5. **El límite (30 s).** Probar con una fecha sin dato: el sistema responde que **no avisa** y que un día sin dato no es 0 mm. Cerrar con «Darme de baja».

## Qué decir de lo que viene

- Los tres canales ya están separados y pasan por un único punto de entrega: conectar WhatsApp (Cloud API de Meta) y un correo real es reemplazar ese punto, sin tocar las reglas.
- Faltan cosas que no son de código: una cuenta de empresa verificada, un número dedicado, plantillas aprobadas, un dominio de correo y definir con quién se coordina (Defensa Civil u otra área), quién responde por cada aviso y cómo se resguardan los datos personales.
- Predicción, zonas inundables y evacuaciones **no** están: no hay datos oficiales ni relieve, y no se inventan (ver `docs/decisiones/temas/avisos-a-la-poblacion.md`).

## Si algo falla

- **El celular dice que la demostración está apagada:** falta `ALERTS_DEMO=true` en el `.env` (reiniciar el backend).
- **«Los avisos están deshabilitados»:** falta `ALERTS_SECRET`.
- **La vista previa dice «sin dato»:** esa fecha no tiene dato en la estación elegida; usar el botón del día de ejemplo.
- **Error de tabla o columna:** correr `alembic upgrade head` (migraciones 0006 y 0007).
