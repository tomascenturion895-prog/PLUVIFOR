import { Link } from 'react-router-dom'
import { useIdioma } from '../i18n/usar-idioma'

export { Mapa } from './Map'

export function NoEncontrada() {
  const { t } = useIdioma()
  return (
    <section>
      <h2>{t('error.noEncontradaTitulo')}</h2>
      <p>
        {t('error.noEncontradaTexto')} <Link to="/">{t('error.volverInicio')}</Link>.
      </p>
    </section>
  )
}
