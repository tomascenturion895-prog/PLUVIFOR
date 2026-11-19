import type { DataCategory, RainState } from '../api/types'
import { ADVERTENCIAS, type CodigoAdvertencia } from './insignias-datos'
import './Insignias.css'

interface Definicion {
  clase: string
  simbolo: string
  texto: string
  /** Explicación para lectores de pantalla y para el atributo title. */
  descripcion: string
}

/** Un hueco no es 0 mm: ninguna de estas definiciones usa el texto «0» ni el color de un dato. */
const ESTADOS: Record<RainState, Definicion> = {
  dato: {
    clase: 'dato',
    simbolo: '●',
    texto: 'Dato',
    descripcion: 'Hay una medición para este día.',
  },
  sin_fila: {
    clase: 'sin-dato',
    simbolo: '∅',
    texto: 'Sin dato',
    descripcion: 'La fuente no tiene este día. No significa que no haya llovido.',
  },
  fila_sin_valor: {
    clase: 'sin-valor',
    simbolo: '◌',
    texto: 'Fila sin valor',
    descripcion: 'La fuente tiene el día pero sin un valor. No significa que no haya llovido.',
  },
}

const CATEGORIAS: Record<DataCategory, Definicion> = {
  observado: {
    clase: 'observado',
    simbolo: '▣',
    texto: 'Observado',
    descripcion: 'Medido por una estación o un reporte.',
  },
  referencia: {
    clase: 'referencia',
    simbolo: '◆',
    texto: 'Referencia',
    descripcion:
      'Valor de referencia (por ejemplo, una normal climática). No se suma a lo observado.',
  },
  estimado: {
    clase: 'estimado',
    simbolo: '≈',
    texto: 'Estimado',
    descripcion: 'Calculado, no medido. Nunca se suma ni se promedia con lo observado.',
  },
}

const SIMULADO: Definicion = {
  clase: 'simulado',
  simbolo: '⚙',
  texto: 'Simulado',
  descripcion:
    'Lectura inventada por un simulador, no de un sensor real. Nunca se suma a lo observado.',
}

function Insignia({ definicion, tipo }: { definicion: Definicion; tipo: string }) {
  return (
    <span
      className={`insignia insignia-${definicion.clase}`}
      data-tipo={tipo}
      title={definicion.descripcion}
    >
      <span className="insignia-simbolo" aria-hidden="true">
        {definicion.simbolo}
      </span>
      <span>{definicion.texto}</span>
      <span className="sr-only">. {definicion.descripcion}</span>
    </span>
  )
}

export function InsigniaEstado({ estado }: { estado: RainState }) {
  return <Insignia definicion={ESTADOS[estado]} tipo="estado" />
}

export function InsigniaCategoria({ categoria }: { categoria: DataCategory }) {
  return <Insignia definicion={CATEGORIAS[categoria]} tipo="categoria" />
}

/**
 * Advertencia de comparabilidad. Si llega un código que no conocemos se muestra con el mensaje de
 * la API (o el código) en lugar de ocultarla: una advertencia nunca se pierde en silencio.
 */
/** Rótulo de las lecturas del simulador de dispositivos (SCRUM-94). */
export function InsigniaSimulado() {
  return <Insignia definicion={SIMULADO} tipo="categoria" />
}

export function InsigniaAdvertencia({ codigo, mensaje }: { codigo: string; mensaje?: string }) {
  const conocida = ADVERTENCIAS[codigo as CodigoAdvertencia] as
    { texto: string; descripcion: string } | undefined
  const definicion: Definicion = {
    clase: 'advertencia',
    simbolo: '⚠',
    texto: conocida?.texto ?? mensaje ?? codigo,
    descripcion: mensaje ?? conocida?.descripcion ?? 'Advertencia de calidad del dato.',
  }
  return <Insignia definicion={definicion} tipo="advertencia" />
}
