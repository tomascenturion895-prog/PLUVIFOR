import type { ReactNode } from 'react'

export function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  return (
    <p role="status" className="estado estado-cargando">
      {texto}
    </p>
  )
}

export function ErrorEstado({
  mensaje,
  onReintentar,
}: {
  mensaje: string
  onReintentar?: () => void
}) {
  return (
    <div role="alert" className="estado estado-error">
      <p>{mensaje}</p>
      {onReintentar && (
        <button type="button" onClick={onReintentar}>
          Reintentar
        </button>
      )}
    </div>
  )
}

export function Vacio({ children }: { children: ReactNode }) {
  return <p className="estado estado-vacio">{children}</p>
}
