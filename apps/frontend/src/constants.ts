/** Leyenda obligatoria: debe estar visible en todas las pantallas. */
export const LEYENDA_PROTOTIPO =
  'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial'

/** Secciones de la navegación, en el orden en que se muestran. */
export const SECCIONES = [
  { ruta: '/', nombre: 'Inicio' },
  { ruta: '/mapa', nombre: 'Mapa' },
  { ruta: '/estacion', nombre: 'Estación' },
  { ruta: '/comparador', nombre: 'Comparador' },
  { ruta: '/parte', nombre: 'Parte pluvial' },
  { ruta: '/importar', nombre: 'Importar y auditar' },
  { ruta: '/salud', nombre: 'Salud de la red' },
  { ruta: '/ayuda', nombre: 'Ayuda' },
] as const

/** Fecha de corte de los datos: no se consultan ni muestran días posteriores. */
export const FECHA_CORTE = '2026-10-31'
