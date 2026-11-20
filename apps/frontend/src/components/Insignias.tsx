import type { DataCategory, RainState } from '../api/types'
import { useIdioma } from '../i18n/usar-idioma'
import type { ClaveTraduccion } from '../i18n/traducciones/es'
import { ADVERTENCIAS, ADVERTENCIAS_CALIDAD, type CodigoAdvertencia } from './insignias-datos'
import './Insignias.css'

interface Definicion {
  clase: string
  simbolo: string
  texto: string
  /** Explicación para lectores de pantalla y para el atributo title. */
  descripcion: string
}

const CLAVE_ESTADO: Record<
  RainState,
  { clase: string; simbolo: string; texto: ClaveTraduccion; desc: ClaveTraduccion }
> = {
  dato: {
    clase: 'dato',
    simbolo: '●',
    texto: 'insignia.estado.dato',
    desc: 'insignia.estado.dato.desc',
  },
  sin_fila: {
    clase: 'sin-dato',
    simbolo: '∅',
    texto: 'insignia.estado.sin_fila',
    desc: 'insignia.estado.sin_fila.desc',
  },
  fila_sin_valor: {
    clase: 'sin-valor',
    simbolo: '◌',
    texto: 'insignia.estado.fila_sin_valor',
    desc: 'insignia.estado.fila_sin_valor.desc',
  },
}

const CLAVE_CATEGORIA: Record<
  DataCategory,
  { clase: string; simbolo: string; texto: ClaveTraduccion; desc: ClaveTraduccion }
> = {
  observado: {
    clase: 'observado',
    simbolo: '▣',
    texto: 'insignia.categoria.observado',
    desc: 'insignia.categoria.observado.desc',
  },
  referencia: {
    clase: 'referencia',
    simbolo: '◆',
    texto: 'insignia.categoria.referencia',
    desc: 'insignia.categoria.referencia.desc',
  },
  estimado: {
    clase: 'estimado',
    simbolo: '≈',
    texto: 'insignia.categoria.estimado',
    desc: 'insignia.categoria.estimado.desc',
  },
}

const CLAVE_ADV: Record<CodigoAdvertencia, { texto: ClaveTraduccion; desc: ClaveTraduccion }> = {
  horario_corte_distinto: {
    texto: 'adv.horario_corte_distinto',
    desc: 'adv.horario_corte_distinto.desc',
  },
  observado_vs_estimado: {
    texto: 'adv.observado_vs_estimado',
    desc: 'adv.observado_vs_estimado.desc',
  },
  cobertura_despareja: {
    texto: 'adv.cobertura_despareja',
    desc: 'adv.cobertura_despareja.desc',
  },
  dato_sin_validar: {
    texto: 'adv.dato_sin_validar',
    desc: 'adv.dato_sin_validar.desc',
  },
  ceros_prolongados: {
    texto: 'adv.ceros_prolongados',
    desc: 'adv.ceros_prolongados.desc',
  },
  inconsistente_con_vecinas: {
    texto: 'adv.inconsistente_con_vecinas',
    desc: 'adv.inconsistente_con_vecinas.desc',
  },
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
  const { t } = useIdioma()
  const c = CLAVE_ESTADO[estado]
  return (
    <Insignia
      definicion={{ clase: c.clase, simbolo: c.simbolo, texto: t(c.texto), descripcion: t(c.desc) }}
      tipo="estado"
    />
  )
}

export function InsigniaCategoria({ categoria }: { categoria: DataCategory }) {
  const { t } = useIdioma()
  const c = CLAVE_CATEGORIA[categoria]
  return (
    <Insignia
      definicion={{ clase: c.clase, simbolo: c.simbolo, texto: t(c.texto), descripcion: t(c.desc) }}
      tipo="categoria"
    />
  )
}

/** Rótulo de las lecturas del simulador de dispositivos (SCRUM-94). */
export function InsigniaSimulado() {
  const { t } = useIdioma()
  return (
    <Insignia
      definicion={{
        clase: 'simulado',
        simbolo: '⚙',
        texto: t('insignia.categoria.simulado'),
        descripcion: t('insignia.categoria.simulado.desc'),
      }}
      tipo="categoria"
    />
  )
}

/**
 * Advertencia de comparabilidad. Si llega un código que no conocemos se muestra con el mensaje de
 * la API (o el código) en lugar de ocultarla: una advertencia nunca se pierde en silencio.
 */
export function InsigniaAdvertencia({ codigo, mensaje }: { codigo: string; mensaje?: string }) {
  const { t } = useIdioma()
  const adv = codigo in ADVERTENCIAS ? CLAVE_ADV[codigo as CodigoAdvertencia] : undefined
  const calidad = ADVERTENCIAS_CALIDAD[codigo]
  const definicion: Definicion = {
    clase: 'advertencia',
    simbolo: '⚠',
    texto: adv ? t(adv.texto) : (calidad?.texto ?? mensaje ?? codigo),
    descripcion:
      mensaje ?? (adv ? t(adv.desc) : (calidad?.descripcion ?? 'Advertencia de calidad del dato.')),
  }
  return <Insignia definicion={definicion} tipo="advertencia" />
}
