import { useEffect, useId, useState } from 'react'
import { useIdioma } from '../../i18n/usar-idioma'
import Icono from '../../material/Icono'
import {
  aplicar,
  almacenLocal,
  CONTRASTES,
  guardar,
  leer,
  MOVIMIENTOS,
  porDefecto,
  TEXTOS,
  type Preferencias,
} from './a11y-datos'

function sistemaPideMenosMovimiento(): boolean {
  return typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false
}

/** Tamaño de texto, alto contraste y reducción de movimiento, guardados en el dispositivo. */
export default function PanelAccesibilidad() {
  const id = useId()
  const { t } = useIdioma()
  const [abierto, setAbierto] = useState(false)
  const [prefs, setPrefs] = useState<Preferencias>(() =>
    leer(almacenLocal(), porDefecto(sistemaPideMenosMovimiento())),
  )

  const etiquetaTexto = {
    normal: t('a11y.texto.normal'),
    grande: t('a11y.texto.grande'),
    'muy-grande': t('a11y.texto.muyGrande'),
  } as const
  const etiquetaContraste = {
    normal: t('a11y.contraste.normal'),
    alto: t('a11y.contraste.alto'),
  } as const
  const etiquetaMovimiento = {
    normal: t('a11y.movimiento.normal'),
    reducido: t('a11y.movimiento.reducido'),
  } as const

  useEffect(() => {
    aplicar(document.documentElement, prefs)
  }, [prefs])

  function cambiar(cambio: Partial<Preferencias>) {
    const nuevas = { ...prefs, ...cambio }
    setPrefs(nuevas)
    guardar(almacenLocal(), nuevas)
  }

  function restablecer() {
    const base = porDefecto(sistemaPideMenosMovimiento())
    setPrefs(base)
    guardar(almacenLocal(), base)
  }

  return (
    <div className="a11y">
      <button
        type="button"
        className="a11y-boton"
        aria-expanded={abierto}
        aria-controls={id}
        onClick={() => setAbierto((v) => !v)}
      >
        <Icono nombre="accesibilidad" />
        {t('a11y.boton')}
      </button>
      {abierto && (
        <section id={id} className="a11y-panel" aria-label={t('a11y.panel')}>
          <Grupo
            nombre={t('a11y.texto')}
            opciones={TEXTOS}
            etiquetas={etiquetaTexto}
            valor={prefs.texto}
            alCambiar={(texto) => cambiar({ texto })}
          />
          <Grupo
            nombre={t('a11y.contraste')}
            opciones={CONTRASTES}
            etiquetas={etiquetaContraste}
            valor={prefs.contraste}
            alCambiar={(contraste) => cambiar({ contraste })}
          />
          <Grupo
            nombre={t('a11y.movimiento')}
            opciones={MOVIMIENTOS}
            etiquetas={etiquetaMovimiento}
            valor={prefs.movimiento}
            alCambiar={(movimiento) => cambiar({ movimiento })}
          />
          <p className="nota">{t('a11y.nota')}</p>
          <button type="button" onClick={restablecer}>
            {t('a11y.restablecer')}
          </button>
        </section>
      )}
    </div>
  )
}

function Grupo<T extends string>({
  nombre,
  opciones,
  etiquetas,
  valor,
  alCambiar,
}: {
  nombre: string
  opciones: readonly T[]
  etiquetas: Record<T, string>
  valor: T
  alCambiar: (v: T) => void
}) {
  return (
    <fieldset className="a11y-grupo">
      <legend>{nombre}</legend>
      {opciones.map((o) => (
        <label key={o}>
          <input
            type="radio"
            name={nombre}
            value={o}
            checked={valor === o}
            onChange={() => alCambiar(o)}
          />{' '}
          {etiquetas[o]}
        </label>
      ))}
    </fieldset>
  )
}
