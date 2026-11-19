# Preguntas pendientes para CITF y la mentoría

> PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial

Borrador de SCRUM-28. **Este documento no envía nada:** alguien del equipo (Tomás o Samuel) tiene que mandarlo y anotar la fecha de envío y de respuesta. Cada pregunta nace de algo que ya apareció en el trabajo del Sprint 0; ninguna es hipotética.

Entrega del prototipo: viernes 20/11 18:00 o sábado 21/11 10:00 (**sin confirmar**; es la primera pregunta de la lista).

| # | Eje | Pregunta | Por qué importa | Respuesta | Fecha envío / respuesta |
|---|---|---|---|---|---|
| 1 | Demostración | ¿La entrega es el viernes 20/11 a las 18:00 o el sábado 21/11 a las 10:00? ¿Hay que presentar en vivo o alcanza con el repositorio y la demo? | Define el congelamiento de código (viernes 12:00) y el plan de las últimas 48 horas. | pendiente | |
| 2 | Demostración | ¿La demo puede correr sin internet, con datos locales? ¿Quién es el «equipo offline» (jurado, equipo de campo, cargadores)? | Decide cuánto trabajo sin conexión se hace (demo local solamente, o PWA con cola de carga). | pendiente | |
| 3 | Datos | ¿Pueden darnos las coordenadas de las estaciones de la red provincial y de la UPCA que siguen pendientes? | No las inventamos: sin coordenadas esas estaciones no salen en el mapa. | pendiente | |
| 4 | Datos | ¿Qué licencia o condiciones de uso tienen los datos del INA (Alerta Hidrológico)? ¿A qué provincia pertenecen las tres estaciones sobre el río Bermejo? ¿Qué significan los códigos de disponibilidad `NRT`, `RT`, `C` y `H`? | Falta confirmarlo antes de publicar o cargar esas series (ver `docs/fuentes/ina.md`). | pendiente | |
| 5 | Datos | El servicio del SIGA/INTA cambió de dirección y la anterior dejó de responder. ¿Es estable la actual? ¿Hay un canal oficial para pedir las series? | Nuestro script la redescubre solo, pero depende de un nombre que puede volver a cambiar. | pendiente | |
| 6 | Problema / límites | ¿Cómo quieren que se trate el horario de corte (07:00 contra 09:00) al comparar redes? ¿Alcanza con la advertencia o hay que normalizar? | Hoy solo advertimos; no sumamos ni promediamos redes distintas. | pendiente | |
| 7 | Usuario | ¿Quiénes son los usuarios que tienen que ver el reporte (técnicos, autoridades, público)? ¿A qué canales habría que avisar cuando hay un evento intenso? | Define si hace falta aviso y a quién; hoy solo hay alertas descriptivas, sin canales definidos. | pendiente | |
| 8 | Aporte tecnológico | ¿Es un requisito usar Go en el servidor? ¿Alguien del equipo evaluador lo espera? | Hoy el backend es Python/FastAPI; migrar antes de la entrega pone en riesgo el plazo. | pendiente | |

## Fuera de alcance

No preguntamos por alturas de ríos, caudales, zonas de riesgo ni evacuaciones: son de otros desafíos.
