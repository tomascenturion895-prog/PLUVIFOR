import type { ReactNode } from 'react'
import { useIdioma } from '../i18n/usar-idioma'

export function Cargando({ texto }: { texto?: string }) {
  const { t } = useIdioma()
  return (
    <div role="status" className="estado estado-cargando">
      <md-linear-progress indeterminate aria-hidden="true" />
      <p>{texto ?? t('estado.cargando')}</p>
    </div>
  )
}

export function ErrorEstado({
  mensaje,
  onReintentar,
}: {
  mensaje: string
  onReintentar?: () => void
}) {
  const { t } = useIdioma()
  return (
    <div role="alert" className="estado estado-error">
      <p>{mensaje}</p>
      {onReintentar && (
        <button type="button" onClick={onReintentar}>
          {t('estado.reintentar')}
        </button>
      )}
    </div>
  )
}

export function Vacio({ children }: { children: ReactNode }) {
  return <p className="estado estado-vacio">{children}</p>
}
