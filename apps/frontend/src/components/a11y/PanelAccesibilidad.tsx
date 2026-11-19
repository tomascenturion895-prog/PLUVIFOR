import { useEffect, useId, useState } from 'react'
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

const ETIQUETA_TEXTO = { normal: 'Normal', grande: 'Grande', 'muy-grande': 'Muy grande' } as const
const ETIQUETA_CONTRASTE = { normal: 'Normal', alto: 'Alto contraste' } as const
const ETIQUETA_MOVIMIENTO = { normal: 'Normal', reducido: 'Reducir movimiento' } as const

function sistemaPideMenosMovimiento(): boolean {
  return typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false
}

/** Tamaño de texto, alto contraste y reducción de movimiento, guardados en el dispositivo. */
export default function PanelAccesibilidad() {
  const id = useId()
  const [abierto, setAbierto] = useState(false)
  const [prefs, setPrefs] = useState<Preferencias>(() =>
    leer(almacenLocal(), porDefecto(sistemaPideMenosMovimiento())),
  )

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
        Accesibilidad
      </button>
      {abierto && (
        <section id={id} className="a11y-panel" aria-label="Opciones de accesibilidad">
          <Grupo
            nombre="Tamaño del texto"
            opciones={TEXTOS}
            etiquetas={ETIQUETA_TEXTO}
            valor={prefs.texto}
            alCambiar={(texto) => cambiar({ texto })}
          />
          <Grupo
            nombre="Contraste"
            opciones={CONTRASTES}
            etiquetas={ETIQUETA_CONTRASTE}
            valor={prefs.contraste}
            alCambiar={(contraste) => cambiar({ contraste })}
          />
          <Grupo
            nombre="Movimiento"
            opciones={MOVIMIENTOS}
            etiquetas={ETIQUETA_MOVIMIENTO}
            valor={prefs.movimiento}
            alCambiar={(movimiento) => cambiar({ movimiento })}
          />
          <p className="nota">
            Tu elección se guarda en este dispositivo. Los datos se distinguen siempre por su texto,
            su símbolo y el tipo de borde, no solo por el color.
          </p>
          <button type="button" onClick={restablecer}>
            Restablecer
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
