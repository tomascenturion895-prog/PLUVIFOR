# Preguntas para el CITF y la mentoría

PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Borrador para SCRUM-28. **No está enviado**: quien lo envíe debe revisarlo y completar el contexto
que falte. Cada pregunta indica por qué importa y qué se hace mientras no haya respuesta.

## Las 7 preguntas de la tarea

| # | Tema | Pregunta | Mientras no haya respuesta |
|---|---|---|---|
| 1 | Datos del parte del 17/11 | ¿De dónde salen los datos del parte pluvial del 17/11 y podemos usarlos? ¿Hay un archivo o una fuente que nos puedan compartir? | No se usan: el prototipo solo muestra series con fuente y categoría conocidas (SIGA/INTA). |
| 2 | Operador de `formosa-lluvias-production.up.railway.app` | ¿Quién opera ese sitio y con qué permiso o licencia podemos consultar o reutilizar sus datos? | No se consulta ni se copia nada de ese sitio. |
| 3 | Coordenadas de las 34 estaciones | ¿Nos pueden pasar las coordenadas verificadas de las 34 estaciones provinciales? | Las estaciones sin coordenadas quedan como `pendiente`: no entran en el mapa ni en la regla de estaciones vecinas. Nada se inventa. |
| 4 | Perfil RAMF | ¿Qué perfil debe tener la herramienta para el RAMF y qué necesita ver ese perfil? | Se sigue con el alcance de AGENTS.md (consulta, comparación y calidad del dato). |
| 5 | Fecha de entrega | ¿La entrega es el viernes 20/11 a las 18 h o el sábado 21/11 a las 10 h? | Se planifica con la fecha más temprana. |
| 6 | Formato de presentación | ¿Se presenta con póster o con 5 diapositivas? | Se prepara el material más corto y se adapta después. |
| 7 | Tercera fase | ¿Qué se espera de la tercera fase y cuándo se define? | No se agrega alcance fuera del Desafío 2. |

## Preguntas adicionales (opcionales)

| # | Tema | Pregunta | Contexto |
|---|---|---|---|
| 8 | Series del INA | ¿El INA va a cargar las series de lluvia de las estaciones INTA de Formosa (por ejemplo El Colorado, Bartolomé de las Casas) y desde cuándo? | La API del INA las lista, pero hoy devuelve 0 observaciones. Ver `docs/datos/ina_lluvia_formosa.md`. |
| 9 | Acceso al SIGA | ¿Cuál es la forma vigente de consultar las series diarias del SIGA? | El pedido que usa `docs/datos/descargar_siga.py` hoy responde 404. |
| 10 | Horario de corte | ¿A qué hora cierra el «día de lluvia» en cada estación del SIGA (convencionales y automáticas)? | `day_cutoff_local` queda vacío hasta confirmarlo. |

## Cuando haya respuestas

1. Registrar cada respuesta debajo de su pregunta, con fecha y quién respondió.
2. Actualizar `docs/modelo-datos.md` y `AGENTS.md` si cambia alguna regla o la fecha de entrega.
3. Cerrar SCRUM-28 cuando las preguntas estén enviadas y la fecha esté confirmada.
