# Cuentas de usuario (registro e inicio de sesión)

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Hasta ahora la escritura (importar datos, reportes de campo, avisos) se protegía con **una sola clave compartida** (`ADMIN_API_KEY`), sin saber quién hacía qué. Ahora hay cuentas con roles, y la clave sigue funcionando para scripts y para la demo.

## Roles

| Rol | Cómo se obtiene | Qué puede |
|---|---|---|
| `ciudadano` | Se registra solo en `/cuenta` | Tener una cuenta y gestionar sus suscripciones a avisos. **No** puede cargar datos. |
| `operador` | Lo asigna un administrador | Importar datos, cargar reportes de campo y mandar avisos. |
| `administrador` | El primero, por línea de comandos; los demás, otro administrador | Todo lo anterior y gestionar las cuentas. |

**Quien se registra no elige su rol:** toda cuenta nueva nace como ciudadano (un campo `role` en el pedido se rechaza). Un administrador no puede cambiarse el rol ni desactivarse a sí mismo, así siempre queda al menos uno.

## Crear el primer administrador

La contraseña nunca va en la línea de comandos (quedaría en el historial de la terminal). Desde `apps/backend`, con el entorno virtual activo y la base migrada (`alembic upgrade head`):

```bash
python -m app.cli create-user --email tu@correo.com --role administrador
# Te pide la contraseña (mínimo 10 caracteres) dos veces.
```

Para automatizarlo sin terminal se puede definir la variable `PLUVIFOR_NEW_USER_PASSWORD`. Después ingresá en `/cuenta`; desde ahí asignás roles a los demás.

## Cómo funciona

- **Contraseñas:** se guardan con **scrypt** (biblioteca estándar de Python: no se sumó ninguna dependencia), con una sal distinta por cuenta. Nunca en claro ni en los registros. De 10 a 128 caracteres, sin espacios en los bordes y distinta del correo.
- **Sesiones:** al ingresar se entrega un token aleatorio que se envía como `Authorization: Bearer ...`. **En la base solo queda su resumen SHA-256**, vence a las `SESSION_HOURS` horas (12 por defecto) y se revoca al cerrar sesión, al cambiar el rol o al desactivar la cuenta. En el navegador vive en `sessionStorage` (se pierde al cerrar la pestaña).
- **Fuerza bruta:** 5 intentos fallidos bloquean la cuenta 15 minutos, y `/api/auth` admite pocos pedidos por minuto y por dirección (`RATE_LIMIT_AUTH_PER_MINUTE`). Un correo inexistente y una clave incorrecta responden **lo mismo** y tardan lo mismo.
- **Quién cargó qué:** las importaciones (`import_logs`) y los reportes de campo (`field_reports`) guardan `created_by_user_id`. Queda nulo si se usó la clave de administración o la línea de comandos, y también si después se borra la cuenta.
- **La clave de administración sigue valiendo** para las rutas de escritura (importación, reportes, avisos), pero **no** para gestionar cuentas: eso exige una sesión de administrador.

## Variables de entorno

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `SESSION_HOURS` | `12` | Cuánto dura una sesión |
| `REGISTRATION_OPEN` | `true` | `false` cierra el registro por la API (siguen las altas por línea de comandos) |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Pedidos por minuto y por dirección a `/api/auth` |

## Contrato

Está en `apps/api-go/openapi.yaml`: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/users` y `PATCH /api/users/{id}`. Go reenvía estos pedidos a Python, que es el único que escribe en la base.

## Tablas

`users` (correo único, resumen de la contraseña, rol, si está activa, intentos fallidos y bloqueo) y `auth_sessions` (resumen del token, vencimiento y revocación; se borran con la cuenta). Ver `docs/modelo-datos.md`.

## Qué no hace (pendiente)

- **No hay recuperación de contraseña ni verificación del correo:** haría falta enviar correos reales, que hoy no existen (ver `docs/ingesta-avisos.md`). Un administrador puede desactivar una cuenta, pero hoy no restablece contraseñas.
- **No hay segundo factor.**
- **Registrar un correo ya usado responde 409**, lo que permite saber si un correo tiene cuenta. Se aceptó para el prototipo; con correo real se respondería igual y se avisaría por mail.
- **El token vive en `sessionStorage`**, que un script malicioso en la página podría leer. Una cookie `HttpOnly` con protección contra CSRF sería más segura y queda para cuando el sistema se publique.
- Las sesiones vencidas no se borran de la base automáticamente.
