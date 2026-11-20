import { useIdioma } from '../../i18n/usar-idioma'
import { ATAJOS, type Atajo } from './atajos'

export default function Atajos({
  activo,
  alElegir,
}: {
  activo: Atajo['id'] | null
  alElegir: (atajo: Atajo) => void
}) {
  const { t } = useIdioma()
  return (
    <section className="atajos" aria-label={t('atajos.titulo')}>
      <h3>{t('atajos.titulo')}</h3>
      <ul>
        {ATAJOS.map((a) => (
          <li key={a.id}>
            <button type="button" aria-pressed={activo === a.id} onClick={() => alElegir(a)}>
              {a.nombre}
            </button>
            <span className="nota"> {a.descripcion}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
