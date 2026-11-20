/** Leyenda obligatoria: debe estar visible en todas las pantallas. */
export const LEYENDA_PROTOTIPO =
  'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial'

/** Secciones de la navegación, en el orden en que se muestran. */
export const SECCIONES = [
  { ruta: '/', nombre: 'Inicio', icono: 'inicio' },
  { ruta: '/vista-3d', nombre: 'Vista 3D', icono: 'vista3d' },
  { ruta: '/maqueta', nombre: 'Maqueta', icono: 'maqueta' },
  { ruta: '/mapa', nombre: 'Mapa', icono: 'mapa' },
  { ruta: '/estacion', nombre: 'Estación', icono: 'estacion' },
  { ruta: '/comparador', nombre: 'Comparador', icono: 'comparador' },
  { ruta: '/parte', nombre: 'Parte pluvial', icono: 'parte' },
  { ruta: '/reporte', nombre: 'Reporte de campo', icono: 'reporte' },
  { ruta: '/importar', nombre: 'Importar y auditar', icono: 'importar' },
  { ruta: '/salud', nombre: 'Salud de la red', icono: 'salud' },
  { ruta: '/sensores', nombre: 'Sensores', icono: 'sensores' },
  { ruta: '/avisos', nombre: 'Avisos', icono: 'avisos' },
  { ruta: '/ayuda', nombre: 'Ayuda', icono: 'ayuda' },
] as const

/** Fecha de corte de los datos: no se consultan ni muestran días posteriores. */
export const FECHA_CORTE = '2026-10-31'

/** Tamaño máximo de un archivo a importar (igual que el de la API: 5 MB). */
export const MAX_ARCHIVO_BYTES = 5 * 1024 * 1024

/** Cantidad máxima de estaciones por parte (igual que la API). */
export const MAX_ESTACIONES_PARTE = 20

/** Cantidad máxima de estaciones del comparador. */
export const MAX_ESTACIONES_COMPARADOR = 4
