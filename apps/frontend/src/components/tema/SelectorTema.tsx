import { useEffect, useState } from 'react'
import { useIdioma } from '../../i18n/usar-idioma'
import type { ClaveTraduccion } from '../../i18n/traducciones/es'
import {
  aplicarTema,
  almacenLocal,
  guardarTema,
  leerTema,
  SIMBOLO_TEMA,
  TEMAS,
  type Tema,
} from './tema-datos'

const CLAVE_TEMA_ETIQUETA: Record<Tema, ClaveTraduccion> = {
  claro: 'tema.claro',
  oscuro: 'tema.oscuro',
  daltonico: 'tema.daltonico',
}

const CLAVE_TEMA_DESC: Record<Tema, ClaveTraduccion> = {
  claro: 'tema.claro.desc',
  oscuro: 'tema.oscuro.desc',
  daltonico: 'tema.daltonico.desc',
}

/** Selector de tema (claro, oscuro, daltónico). La elección se guarda en este dispositivo. */
export default function SelectorTema() {
  const [tema, setTema] = useState<Tema>(() => leerTema(almacenLocal()))
  const { t } = useIdioma()

  useEffect(() => {
    aplicarTema(document.documentElement, tema)
  }, [tema])

  function elegir(nuevo: Tema) {
    setTema(nuevo)
    guardarTema(almacenLocal(), nuevo)
  }

  return (
    <fieldset className="selector-tema">
      <legend className="sr-only">{t('tema.etiqueta')}</legend>
      {TEMAS.map((tm) => (
        <label key={tm} className="selector-tema-opcion" title={t(CLAVE_TEMA_DESC[tm])}>
          <input
            type="radio"
            name="tema-de-color"
            value={tm}
            checked={tema === tm}
            onChange={() => elegir(tm)}
          />
          <span className="selector-tema-texto">
            <span aria-hidden="true">{SIMBOLO_TEMA[tm]}</span> {t(CLAVE_TEMA_ETIQUETA[tm])}
          </span>
        </label>
      ))}
    </fieldset>
  )
}
