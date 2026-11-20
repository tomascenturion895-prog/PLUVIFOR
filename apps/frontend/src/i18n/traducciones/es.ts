/** Diccionario base en español (es). Es la fuente de verdad de todas las claves de i18n. */
export const es = {
  // Marca y layout
  'app.subtitulo': 'Reporte pluvial de Formosa',
  'app.leyendaPrototipo':
    'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial',
  'nav.etiqueta': 'Secciones',
  'nav.menu': 'Menú',
  'nav.inicio': 'Inicio',
  'nav.vista3d': 'Vista 3D',
  'nav.maqueta': 'Maqueta',
  'nav.mapa': 'Mapa',
  'nav.estacion': 'Estación',
  'nav.comparador': 'Comparador',
  'nav.parte': 'Parte pluvial',
  'nav.reporte': 'Reporte de campo',
  'nav.importar': 'Importar y auditar',
  'nav.salud': 'Salud de la red',
  'nav.ayuda': 'Ayuda',
  'nav.noEncontrada': 'Página no encontrada',

  // Selector de idioma
  'idioma.etiqueta': 'Idioma de la interfaz',

  // Selector de tema
  'tema.etiqueta': 'Tema de color',
  'tema.claro': 'Claro',
  'tema.oscuro': 'Oscuro',
  'tema.daltonico': 'Daltónico',
  'tema.claro.desc': 'Fondo gris claro, de bajo brillo',
  'tema.oscuro.desc': 'Tema original, fondo oscuro',
  'tema.daltonico.desc': 'Azul y naranja, con íconos y subrayados además del color',

  // Accesibilidad
  'a11y.boton': 'Accesibilidad',
  'a11y.panel': 'Opciones de accesibilidad',
  'a11y.texto': 'Tamaño del texto',
  'a11y.texto.normal': 'Normal',
  'a11y.texto.grande': 'Grande',
  'a11y.texto.muyGrande': 'Muy grande',
  'a11y.contraste': 'Contraste',
  'a11y.contraste.normal': 'Normal',
  'a11y.contraste.alto': 'Alto contraste',
  'a11y.movimiento': 'Movimiento',
  'a11y.movimiento.normal': 'Normal',
  'a11y.movimiento.reducido': 'Reducir movimiento',
  'a11y.nota':
    'Tu elección se guarda en este dispositivo. Los datos se distinguen siempre por su texto, su símbolo y el tipo de borde, no solo por el color.',
  'a11y.restablecer': 'Restablecer',

  // Estados y errores comunes
  'estado.cargando': 'Cargando…',
  'estado.cargando3d': 'Cargando la vista 3D…',
  'estado.reintentar': 'Reintentar',
  'error.inesperado': 'Ocurrió un error inesperado al cargar la vista',
  'error.volverInicio': 'Volver al inicio',
  'error.noEncontradaTitulo': 'Página no encontrada',
  'error.noEncontradaTexto': 'No existe esta dirección.',

  // Insignias de estado y categoría
  'insignia.estado.dato': 'Dato',
  'insignia.estado.dato.desc': 'Hay una medición para este día.',
  'insignia.estado.sin_fila': 'Sin dato',
  'insignia.estado.sin_fila.desc': 'La fuente no tiene este día. No significa que no haya llovido.',
  'insignia.estado.fila_sin_valor': 'Fila sin valor',
  'insignia.estado.fila_sin_valor.desc':
    'La fuente tiene el día pero sin un valor. No significa que no haya llovido.',
  'insignia.categoria.observado': 'Observado',
  'insignia.categoria.observado.desc': 'Medido por una estación o un reporte.',
  'insignia.categoria.referencia': 'Referencia',
  'insignia.categoria.referencia.desc':
    'Valor de referencia (por ejemplo, una normal climática). No se suma a lo observado.',
  'insignia.categoria.estimado': 'Estimado',
  'insignia.categoria.estimado.desc':
    'Calculado, no medido. Nunca se suma ni se promedia con lo observado.',
  'insignia.categoria.simulado': 'Simulado',
  'insignia.categoria.simulado.desc':
    'Escenario sintético para pruebas. Nunca se mezcla con datos observados.',

  // Advertencias de comparabilidad
  'adv.horario_corte_distinto': 'Horario de corte distinto',
  'adv.horario_corte_distinto.desc':
    'Las redes cuentan el día de lluvia en horarios distintos (07:00 o 09:00).',
  'adv.observado_vs_estimado': 'Observado vs. estimado',
  'adv.observado_vs_estimado.desc': 'Se están comparando datos medidos con datos estimados.',
  'adv.cobertura_despareja': 'Cobertura despareja',
  'adv.cobertura_despareja.desc': 'Las series no tienen la misma cantidad de días con dato.',
  'adv.dato_sin_validar': 'Dato sin validar',
  'adv.dato_sin_validar.desc': 'Hay valores que todavía no fueron validados.',
  'adv.ceros_prolongados': 'Racha de ceros',
  'adv.ceros_prolongados.desc':
    'Una racha de 60 días o más en 0 mm: puede ser un problema del sensor.',
  'adv.inconsistente_con_vecinas': 'Inconsistente con vecinas',
  'adv.inconsistente_con_vecinas.desc':
    'Estaciones vecinas registran lluvia mientras esta marca 0 mm.',

  // Inicio (Home)
  'home.titulo': '¿Cuánto llovió, dónde y en qué período?',
  'home.p1.inicio': 'PLUVIFOR responde esa pregunta para la provincia de Formosa y siempre dice ',
  'home.p1.destacado': 'qué tan confiable es cada dato',
  'home.p1.fin': ': de qué estación viene, si es medido o estimado y qué advertencias tiene.',
  'home.p2':
    'Un día sin dato se muestra como «sin dato», nunca como 0 mm: que falte la medición no significa que no haya llovido.',
  'home.figura.aria':
    'Ilustración: barras de lluvia diaria; los días sin dato se dibujan rayados, no como cero.',
  'home.figura.pie':
    'Ilustración, no son datos. Las franjas rayadas son días sin dato: no significan 0 mm.',
  'home.accesos.aria': 'Accesos rápidos',
  'home.acceso.vista3d': 'La provincia en 3D: dónde la lluvia observada y los ríos se cruzan.',
  'home.acceso.maqueta': 'La provincia de un vistazo: tocá un departamento y mirá cuánto llovió.',
  'home.acceso.mapa': 'Las estaciones sobre el mapa, con su acumulado del período.',
  'home.acceso.comparador': 'Compará estaciones y períodos, con sus advertencias.',
  'home.acceso.parte': 'Un texto listo para copiar o imprimir, con la fuente y la calidad.',
  'home.acceso.reporte': 'Cargá la lluvia anotada donde no hay estación.',
  'home.pie.inicio': '¿Dudas sobre un color, un símbolo o una advertencia? Mirá la ',
  'home.pie.fin': '. Los datos llegan hasta el 31/10/2026.',

  // Ayuda (Help)
  'ayuda.titulo': 'Ayuda',
  'ayuda.intro': 'Qué significa cada estado de un día, cada categoría de dato y cada advertencia.',
  'ayuda.estados.titulo': 'Estados de un día',
  'ayuda.estados.dato':
    'Hay una medición para ese día. Un «0 mm» con este estado es lluvia cero medida.',
  'ayuda.estados.sin_fila': 'La fuente no tiene ese día. No significa que no haya llovido.',
  'ayuda.estados.fila_sin_valor':
    'La fuente tiene el día pero sin un valor. Tampoco significa que no haya llovido.',
  'ayuda.estados.nota':
    'Los días sin dato se cuentan aparte y nunca entran como 0 mm en un acumulado.',
  'ayuda.categorias.titulo': 'Categorías del dato',
  'ayuda.categorias.observado': 'Medido por una estación o un reporte.',
  'ayuda.categorias.estimado':
    'Calculado, no medido. Nunca se suma ni se promedia con lo observado.',
  'ayuda.categorias.referencia':
    'Valor de referencia, como una normal climática. Tampoco se mezcla con lo observado.',
  'ayuda.advertencias.titulo': 'Las 6 advertencias de comparabilidad',
  'ayuda.advertencias.intro':
    'Avisan cuando dos datos no se pueden comparar de igual a igual. Son descriptivas: no son alertas de riesgo.',
  'ayuda.otras.titulo': 'Otras cosas para tener en cuenta',
  'ayuda.otras.silencio.inicio': 'Una estación ',
  'ayuda.otras.silencio.destacado': 'en silencio',
  'ayuda.otras.silencio.fin':
    ' es la que dejó de reportar: se ve apagada y nunca con el color de 0 mm.',
  'ayuda.otras.corte': 'Los datos llegan hasta el 31/10/2026; no se usan días posteriores.',
  'ayuda.otras.acumulados':
    'Los acumulados de estaciones distintas no se suman: cada estación tiene el suyo.',
} as const

export type ClaveTraduccion = keyof typeof es
export type Diccionario = Record<ClaveTraduccion, string>
