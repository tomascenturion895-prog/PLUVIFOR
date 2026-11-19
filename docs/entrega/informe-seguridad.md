# Informe de seguridad

> **PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial**

Fecha: **19/11/2026**. Tarea: SCRUM-70. Alcance: backend FastAPI, frontend React y el repositorio. Es una revisión del equipo, **no** una auditoría externa ni una prueba de penetración.

Los PR citados (#29 a #41) estaban abiertos y pendientes de merge al escribir este informe. Hasta que se integren, la columna «Estado» describe lo que hay en esas ramas, no en `main`.

## Checklist

| Control | Estado | Evidencia |
|---|---|---|
| **Secretos fuera del código** | Cumple | `.env` ignorado por Git; `.env.example` solo con nombres y valores de ejemplo (`docs/seguridad-secretos.md`). Revisión del historial abajo. |
| **CORS** | Cumple | Solo los orígenes de `CORS_ORIGINS`, sin `*` (la configuración lo rechaza), solo `GET` y `POST`. Pruebas en `tests/test_security.py` (#41). |
| **Escrituras protegidas** | Cumple, con límites | Importar y confirmar exigen `X-API-Key`, comparada en tiempo constante; sin clave configurada la escritura queda deshabilitada (403, cerrado por defecto). Pruebas en `tests/test_admin_key.py` (#30). |
| **Validación de archivos** | Cumple | Extensión `.csv`, archivo vacío, tamaño máximo (5 MB), contenido de texto (se rechazan los binarios disfrazados de `.csv`, por firma y por bytes nulos), y rechazo de texto que empieza con `=`, `+`, `-` o `@` (inyección de fórmulas al abrir el CSV en una planilla). Cada fila rechazada lleva su motivo. Pruebas en `tests/test_upload_security.py` (#31). |
| **Errores sin detalles internos** | Cumple | Formato único de error; un error interno forzado no muestra SQL, rutas ni traza; los errores de validación no repiten el valor recibido. Pruebas en `tests/test_errors.py` y `tests/test_security.py`. |
| **Encabezados de seguridad y tamaño de pedidos** | Cumple | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP cerrada, HSTS en producción; pedidos JSON de hasta 64 KB (#41). |
| **Inyección SQL** | Cumple | Todo el acceso a datos pasa por el ORM (SQLAlchemy); no hay SQL armado con texto. |
| **Dependencias** | Cumple | Sin vulnerabilidades conocidas en `pip-audit` ni `npm audit` (`docs/entrega/auditoria-dependencias.md`). |
| **Documentación de la API en producción** | Cumple | `/docs` y `/openapi.json` se apagan con `APP_ENV=production`. |
| **Clave de administración en el navegador** | Cumple | Se escribe en un campo de contraseña, vive solo en memoria de la pantalla, no se guarda en el navegador ni viaja en la URL (#38). |

## Revisión del historial de Git

- **Escaneo en CI:** el workflow «Secretos» corre gitleaks en cada Pull Request y en cada push a `main` (`.github/workflows/secretos.yml`, configuración en `.gitleaks.toml`).
- **Revisión adicional del 19/11/2026:** se recorrieron los **84 commits de todas las ramas** (21.936 líneas agregadas) buscando patrones de claves de AWS, GitHub, Slack y OpenAI, llaves privadas y asignaciones del tipo `password/secret/token/api_key = «valor largo»`. Resultado: **5 coincidencias, todas valores de prueba obvios** dentro de los tests (`clave-larga-de-prueba`, `clave-super-secreta`). No hay archivos `.env`, `.pem`, `.key` ni bases de datos en el historial.
- Esa revisión fue una búsqueda por expresiones regulares hecha a mano, **no** una corrida de gitleaks (la herramienta no estaba instalada en el entorno de trabajo). Vale como complemento del control de CI, no como reemplazo.

## Lo que quedó sin resolver (y por qué)

| Pendiente | Riesgo | Por qué no se resolvió | Qué haría falta |
|---|---|---|---|
| **Límite de peticiones por dirección** (SCRUM-68) | Alguien puede saturar la API con muchos pedidos | Tarea marcada como recortable; hace falta decidir si el límite va en la API o en el hosting | Implementarlo (o configurarlo en el servicio de despliegue) y probarlo |
| **Una sola clave compartida** para administrar | Quien la tenga puede importar; no hay usuarios ni registro de quién cargó | Un prototipo no necesita cuentas; la clave se rota cambiando la variable de entorno | Usuarios o un proveedor de identidad, si el sistema pasara a producción |
| **HTTPS** | La clave viaja en un encabezado: sin HTTPS se podría capturar | Depende del hosting elegido (SCRUM-57 y SCRUM-79), todavía sin desplegar | Publicar solo con HTTPS; ya hay HSTS en producción |
| **Encabezados del frontend** | La CSP y demás encabezados cubren la API, no la página estática | Los pone el servicio que aloje el frontend | Configurarlos en el hosting |
| **Auditoría de la API en Go** | — | `apps/api-go/` no existe; la decisión sobre Go sigue pendiente | Repetir estos controles si se crea |
| **Dependencias transitivas del backend sin bloqueo** | Una instalación futura podría traer otra versión | Requiere una herramienta nueva (`pip-compile`) | Generar un `requirements.lock` |
| **Auditorías de dependencias fuera del CI** | Una vulnerabilidad nueva pasaría inadvertida | No se tocaron los flujos de CI sin acordarlo | Sumar `npm audit` y `pip-audit` a `ci.yml` |
| **Los importes por API no dejan registro de la auditoría** | Una auditoría (sin guardar) no queda en el historial | Decisión de diseño: `POST /api/import/audit` no escribe nada | Documentado en el PR #32; solo las confirmaciones quedan en `import_logs` |
| **Pruebas con PostgreSQL** (SCRUM-61) | Un comportamiento distinto al de SQLite | No se probó contra PostgreSQL | Correr la suite con `DATABASE_URL` de PostgreSQL |

## Conclusión

No se encontraron vulnerabilidades conocidas en las dependencias ni secretos en el historial, y los controles de la API que se pueden verificar con pruebas están cubiertos. Quedan pendientes el límite de peticiones, el despliegue con HTTPS y los encabezados del frontend, que dependen del hosting. Mientras eso no esté resuelto, el prototipo **no** debería publicarse con datos o escrituras abiertas a Internet.
