import { useId } from 'react'
import { useIdioma } from '../../i18n/usar-idioma'
import { esIdioma, IDIOMAS, NOMBRE_IDIOMA } from '../../i18n/idioma-datos'

/** Selector de idioma (es, en, gn, wlv, tob). La elección se guarda en este dispositivo. */
export default function SelectorIdioma() {
  const id = useId()
  const { idioma, cambiarIdioma, t } = useIdioma()

  return (
    <div className="selector-idioma">
      <label htmlFor={id} className="sr-only">
        {t('idioma.etiqueta')}
      </label>
      <span className="selector-idioma-icono" aria-hidden="true">
        🌐
      </span>
      <select
        id={id}
        className="selector-idioma-select"
        value={idioma}
        aria-label={t('idioma.etiqueta')}
        onChange={(e) => {
          if (esIdioma(e.target.value)) cambiarIdioma(e.target.value)
        }}
      >
        {IDIOMAS.map((codigo) => (
          <option key={codigo} value={codigo}>
            {NOMBRE_IDIOMA[codigo]}
          </option>
        ))}
      </select>
    </div>
  )
}
