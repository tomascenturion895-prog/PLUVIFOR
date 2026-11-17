# Política de secretos

Un secreto es cualquier dato que da acceso a algo: contraseñas, claves de API, tokens, llaves privadas, cadenas de conexión con usuario y clave, la clave de administrador del sistema. **Ninguno se sube al repositorio, nunca**, ni siquiera "por un rato" ni en un repositorio privado.

## Dónde viven los secretos

| Dónde | Qué va |
|---|---|
| `.env` (local, **ignorado por Git**) | Los valores reales de cada persona en su computadora. |
| `.env.example` (versionado) | Solo los **nombres** de las variables y valores de ejemplo, sin secretos reales. |
| Variables del servicio de despliegue | Los valores reales de producción (se cargan en el panel del hosting). |
| Secretos de GitHub Actions | Los valores que necesite el CI (hoy no hay ninguno). |

Reglas:

1. `.env` está en `.gitignore`. Si `git status` lo muestra, **no lo agregues**.
2. Al sumar una variable nueva, se agrega su nombre a `.env.example` con un valor de ejemplo (nunca el real).
3. La clave de administrador (`ADMIN_API_KEY`) en producción debe ser larga y aleatoria; en desarrollo puede quedar vacía.
4. No se pegan secretos en chats de IA, capturas de pantalla, issues, PRs ni mensajes del grupo.
5. El código nunca imprime secretos en los logs ni los devuelve en una respuesta.

## Cómo se controla

Hay dos controles automáticos con el mismo escáner (**gitleaks**, configuración en `.gitleaks.toml`):

1. **Antes de cada commit** (en tu computadora), con `pre-commit`:

   ```bash
   pip install pre-commit
   pre-commit install        # una sola vez por clon del repositorio
   pre-commit run --all-files   # para correrlo a mano
   ```

   Si detecta un secreto, el commit se frena y muestra el archivo y la línea.

2. **En cada Pull Request** (GitHub Actions, workflow «Secretos»). Si encuentra algo, el check falla y el PR no se puede integrar.

Además, en GitHub conviene activar *Settings → Code security → Secret scanning* y *Push protection*.

## Qué hacer si se subió un secreto

Borrar el archivo o el commit **no alcanza**: el secreto queda en el historial y se puede copiar.

1. **Revocar o rotar el secreto de inmediato** (generar una clave nueva y desactivar la anterior).
2. Avisar al equipo.
3. Quitarlo del código y cargar el valor nuevo en `.env` / variables del servicio.
4. Si hace falta, limpiar el historial (consultar antes: reescribir historial afecta a todas las ramas).

## Falsos positivos

Si el escáner marca algo que no es un secreto, se agrega una excepción **puntual** en `.gitleaks.toml` (por ruta o por huella) y se explica en el PR por qué. No se desactiva el escáner.
