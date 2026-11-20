import type { Diccionario } from './es'

/** English (en) translations. */
export const en: Diccionario = {
  // Brand and layout
  'app.subtitulo': 'Formosa rainfall report',
  'app.leyendaPrototipo': 'PROTOTYPE · AI LAB Misión: Código Formosa · not an official tool',
  'nav.etiqueta': 'Sections',
  'nav.menu': 'Menu',
  'nav.inicio': 'Home',
  'nav.vista3d': '3D View',
  'nav.maqueta': 'Model',
  'nav.mapa': 'Map',
  'nav.estacion': 'Station',
  'nav.comparador': 'Compare',
  'nav.parte': 'Rainfall bulletin',
  'nav.reporte': 'Field report',
  'nav.importar': 'Import & audit',
  'nav.salud': 'Network health',
  'nav.sensores': 'Sensors',
  'nav.cuenta': 'Account',
  'nav.avisos': 'Alerts',
  'nav.ayuda': 'Help',
  'nav.noEncontrada': 'Page not found',

  // Language selector
  'idioma.etiqueta': 'Interface language',

  // Theme selector
  'tema.etiqueta': 'Color theme',
  'tema.claro': 'Light',
  'tema.oscuro': 'Dark',
  'tema.daltonico': 'Colorblind',
  'tema.claro.desc': 'Soft light gray background, low glare',
  'tema.oscuro.desc': 'Original dark theme',
  'tema.daltonico.desc': 'Blue and orange palette, with icons and underlines beyond color',

  // Accessibility
  'a11y.boton': 'Accessibility',
  'a11y.panel': 'Accessibility options',
  'a11y.texto': 'Text size',
  'a11y.texto.normal': 'Normal',
  'a11y.texto.grande': 'Large',
  'a11y.texto.muyGrande': 'Extra large',
  'a11y.contraste': 'Contrast',
  'a11y.contraste.normal': 'Normal',
  'a11y.contraste.alto': 'High contrast',
  'a11y.movimiento': 'Motion',
  'a11y.movimiento.normal': 'Normal',
  'a11y.movimiento.reducido': 'Reduce motion',
  'a11y.nota':
    'Your choice is saved on this device. Data is always distinguished by text, symbol, and border style, not by color alone.',
  'a11y.restablecer': 'Reset',

  // Common states and errors
  'estado.cargando': 'Loading…',
  'estado.cargando3d': 'Loading 3D view…',
  'estado.reintentar': 'Retry',
  'error.inesperado': 'An unexpected error occurred while loading the view',
  'error.volverInicio': 'Back to home',
  'error.noEncontradaTitulo': 'Page not found',
  'error.noEncontradaTexto': 'This address does not exist.',

  // State and category badges
  'insignia.estado.dato': 'Data',
  'insignia.estado.dato.desc': 'There is a measurement for this day.',
  'insignia.estado.sin_fila': 'No data',
  'insignia.estado.sin_fila.desc':
    'The source does not have this day. It does not mean it did not rain.',
  'insignia.estado.fila_sin_valor': 'Row without value',
  'insignia.estado.fila_sin_valor.desc':
    'The source has the day but without a value. It does not mean it did not rain.',
  'insignia.categoria.observado': 'Observed',
  'insignia.categoria.observado.desc': 'Measured by a station or field report.',
  'insignia.categoria.referencia': 'Reference',
  'insignia.categoria.referencia.desc':
    'Reference value (for example, a climate normal). Never added to observed data.',
  'insignia.categoria.estimado': 'Estimated',
  'insignia.categoria.estimado.desc':
    'Calculated, not measured. Never added to or averaged with observed data.',
  'insignia.categoria.simulado': 'Simulated',
  'insignia.categoria.simulado.desc':
    'Synthetic scenario for testing. Never mixed with observed data.',

  // Comparability warnings
  'adv.horario_corte_distinto': 'Different cutoff time',
  'adv.horario_corte_distinto.desc':
    'Networks measure the rainfall day with different cutoff times (07:00 vs. 09:00).',
  'adv.observado_vs_estimado': 'Observed vs. estimated',
  'adv.observado_vs_estimado.desc': 'Compares measured data with calculated data.',
  'adv.cobertura_despareja': 'Uneven coverage',
  'adv.cobertura_despareja.desc': 'The series have different proportions of days with data.',
  'adv.dato_sin_validar': 'Unvalidated data',
  'adv.dato_sin_validar.desc': 'Includes readings not yet reviewed.',
  'adv.ceros_prolongados': 'Zero streak',
  'adv.ceros_prolongados.desc': 'Sixty or more consecutive days at 0 mm: check the station.',
  'adv.inconsistente_con_vecinas': 'Inconsistent with neighbors',
  'adv.inconsistente_con_vecinas.desc': 'Differs greatly from nearby stations in the same period.',

  // Home
  'home.titulo': 'How much did it rain, where, and in what period?',
  'home.p1.inicio': 'PLUVIFOR answers that question for the province of Formosa and always shows ',
  'home.p1.destacado': 'how reliable each data point is',
  'home.p1.fin':
    ': which station it comes from, whether it is measured or estimated, and its warnings.',
  'home.p2':
    'A day without data is shown as "no data", never as 0 mm: a missing measurement does not mean it did not rain.',
  'home.figura.aria':
    'Illustration: daily rainfall bars; days without data are drawn striped, not as zero.',
  'home.figura.pie':
    'Illustration, not real data. Striped bars are days without data: they do not mean 0 mm.',
  'home.accesos.aria': 'Quick links',
  'home.acceso.vista3d': 'The province in 3D: where observed rainfall and rivers intersect.',
  'home.acceso.maqueta': 'The province at a glance: tap a department to see how much it rained.',
  'home.acceso.mapa': 'Stations on the map, with their period accumulation.',
  'home.acceso.comparador': 'Compare stations and periods, with their warnings.',
  'home.acceso.parte': 'A text ready to copy or print, with source and data quality.',
  'home.acceso.reporte': 'Record rainfall noted where there is no station.',
  'home.pie.inicio': 'Questions about a color, symbol, or warning? Check ',
  'home.pie.fin': '. Data goes up to 31/10/2026.',

  // Help
  'ayuda.titulo': 'Help',
  'ayuda.intro': 'What each day state, data category, and warning means.',
  'ayuda.estados.titulo': 'Day states',
  'ayuda.estados.dato':
    'There is a measurement for that day. A "0 mm" with this state is measured zero rainfall.',
  'ayuda.estados.sin_fila': 'The source does not have that day. It does not mean it did not rain.',
  'ayuda.estados.fila_sin_valor':
    'The source has the day but without a value. It also does not mean it did not rain.',
  'ayuda.estados.nota':
    'Days without data are counted separately and never enter as 0 mm in an accumulation.',
  'ayuda.categorias.titulo': 'Data categories',
  'ayuda.categorias.observado': 'Measured by a station or field report.',
  'ayuda.categorias.estimado':
    'Calculated, not measured. Never added to or averaged with observed data.',
  'ayuda.categorias.referencia':
    'Reference value, such as a climate normal. Also never mixed with observed data.',
  'ayuda.advertencias.titulo': 'The 6 comparability warnings',
  'ayuda.advertencias.intro':
    'They warn when two datasets cannot be compared on equal terms. They are descriptive, not risk alerts.',
  'ayuda.otras.titulo': 'Other things to keep in mind',
  'ayuda.otras.silencio.inicio': 'A ',
  'ayuda.otras.silencio.destacado': 'silent',
  'ayuda.otras.silencio.fin':
    ' station is one that stopped reporting: it appears dimmed and never with the 0 mm color.',
  'ayuda.otras.corte': 'Data goes up to 31/10/2026; later days are not used.',
  'ayuda.otras.acumulados':
    'Accumulations from different stations are not added together: each station has its own.',

  // Common screen labels
  'comun.desde': 'From',
  'comun.hasta': 'To',
  'comun.estacion': 'Station',
  'comun.estaciones': 'Stations',
  'comun.elegirEstacion': 'Choose a station',
  'comun.fecha': 'Date',
  'comun.lluvia': 'Rainfall',
  'comun.estado': 'Status',
  'comun.zona': 'Zone',
  'comun.fuente': 'Source',
  'comun.acumulado': 'Accumulated',
  'comun.cobertura': 'Coverage',
  'comun.sinDato': 'No data',
  'comun.sinEstaciones': 'No stations loaded.',
  'comun.de': 'of',

  // Station
  'estacion.acumuladoPeriodo': 'Period accumulation',
  'estacion.diasConDato': 'Days with data',
  'estacion.sinDatoSinFila': 'No data (missing row)',
  'estacion.filaSinValor': 'Row without value',
  'estacion.advertenciasCalidad': 'Quality warnings',
  'estacion.verTablaDias': 'View daily table',

  // Network health
  'salud.intro':
    'Which stations are still reporting and which stopped. A silent station does not have "0 mm": it has no data.',
  'salud.resumenAria': 'Network summary',
  'salud.activas': 'active',
  'salud.enSilencio': 'silent',
  'salud.sinDatos': 'no data',
  'salud.tablaCaption': 'Status of each station',
  'salud.ultimaLectura': 'Last reading',
  'salud.sinLecturas': 'No readings',

  // Rainfall bulletin
  'parte.intro':
    'Choose stations and period. The bulletin states the source, category, cutoff date, and quality warnings. A day without data never counts as 0 mm.',
  'parte.generar': 'Generate bulletin',
  'parte.armando': 'Building bulletin…',
  'parte.copiar': 'Copy text',
  'parte.imprimir': 'Print',
  'parte.copiado': 'Text copied. Ready to paste.',
  'parte.copiaError': 'Could not copy automatically: select the bulletin text and copy it.',

  // 3D View
  'v3d.intro':
    'Where observed rainfall and Formosa’s river network intersect, over real department boundaries (IGN). An aid to think about El Niño 2026/27, not a forecast.',
  'v3d.periodoAria': 'Rainfall period',
  'v3d.lluviaDe': 'Rainfall from:',
  'v3d.periodo.nino': 'El Niño 2015/16',
  'v3d.periodo.caso': 'Case 424 & 425',
  'v3d.periodo.registro': 'Full record',
  'v3d.preparando': 'Preparing 3D view…',
  'v3d.leyendo': 'Reading period rainfall…',
  'v3d.sinWebgl': 'This browser cannot render 3D (WebGL). The table below has the same data.',
  'v3d.modoAria': 'What to display on the 3D map',
  'v3d.modo.exposicion': 'Exposure',
  'v3d.modo.pluvial': 'Rainfall',
  'v3d.modo.hidrica': 'River network',
  'v3d.gesto': 'Drag to rotate · scroll or pinch to zoom · tap a department',
  'v3d.leyenda.exposicion': 'Estimated exposure',
  'v3d.leyenda.hidrica': 'Watercourses per area',
  'v3d.clase.baja': 'Low',
  'v3d.clase.media': 'Medium',
  'v3d.clase.alta': 'High',
  'v3d.leyenda.sinDato': 'No data (striped): not "low"',
  'v3d.leyenda.rios': 'Rivers and streams (IGN)',
  'v3d.leyenda.altura': 'Height repeats the class; it is not terrain elevation.',
  'v3d.resumenTitulo': 'Formosa · 9 departments',
  'v3d.elegirDepto': 'Choose a department on the map or in the table.',
  'v3d.departamentos': 'Departments',
  'v3d.departamento': 'Department',
  'v3d.comoSeCalcula': 'How it is calculated',
  'v3d.fuentesPie': 'Sources: SIGA/INTA observed rainfall · IGN cartography. More details in ',
  'v3d.sinDatoConfiable': 'No reliable data',
  'v3d.sinEstacionesDepto': 'There are no stations with rainfall data in this department.',

  // Model & panels
  'maqueta.leyendaAria': 'Model legend',
  'maqueta.datoReal0': '0 mm (measured)',
  'maqueta.sinDatoLeyenda': 'No data (striped): not 0 mm',
  'maqueta.silencioLeyenda': 'Silent station (dimmed)',
  'maqueta.riosLeyenda': 'Watercourses (IGN, cartographic reference)',
  'maqueta.alturaNota':
    'Height repeats the highest individual accumulation in the department; no data stays flat and striped. Terrain elevation: pending verified source.',
  'atajos.titulo': 'Shortcuts',
  'seleccion.titulo': '1 · Your selection',
  'seleccion.todaProvincia': 'Entire province',
  'seleccion.categoria': 'Category',
  'seleccion.estacionesLeyenda': 'Stations (none checked = all in the zone)',
  'seleccion.sinEstacionesZona': 'There are no stations in this zone.',

  // Map
  'mapa.leyendaAria': 'Map legend',
  'mapa.sinDatoLeyenda': 'No data (dashed stroke; gap ≠ 0 mm)',

  // Compare
  'comparador.resultadoAria': 'Comparison result',
  'comparador.advertenciasAria': 'Comparability warnings',
  'comparador.sinAdvertencias': 'No comparability warnings were detected between these series.',
  'comparador.noEvaluadas': 'Warnings that could not be evaluated',
  'comparador.graficoAria': 'Line chart of the series',
  'comparador.boton': 'Compare',

  // Field report
  'reporte.clave': 'Access key',
  'reporte.fechaLluvia': 'Rainfall date',
  'reporte.milimetros': 'Millimeters',
  'reporte.lugar': 'Location',
  'reporte.lugarPlaceholder': 'Police station or locality',
  'reporte.quien': 'Reported by',
  'reporte.ubicacion': 'Coordinates (optional)',
  'reporte.usarUbicacion': 'Use my location',
  'reporte.latitud': 'Latitude',
  'reporte.longitud': 'Longitude',

  // Import & audit
  'importar.tipoLluvia': 'Daily rainfall',
  'importar.tipoEstaciones': 'Station catalog',
  'importar.cargaConfirmada': 'Import confirmed',
  'importar.informeAuditoria': 'Audit report',
  'importar.filasLeidas': 'Rows read',
  'importar.aceptadas': 'Accepted',
  'importar.rechazadas': 'Rejected',
  'importar.nuevas': 'Inserted',
  'importar.actualizadas': 'Updated',
  'importar.filasRechazadas': 'Rejected rows',
  'importar.linea': 'Line',
  'importar.motivo': 'Reason',
  'importar.sinCargas': 'No imports recorded yet.',
  'importar.archivo': 'File',
}
