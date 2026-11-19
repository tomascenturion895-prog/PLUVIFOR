import { useState, type FormEvent } from 'react'
import { ApiError, getReport, getStations } from '../api/client'
import type { Report } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { InsigniaAdvertencia } from '../components/Insignias'
import { FECHA_CORTE, MAX_ESTACIONES_PARTE } from '../constants'
import { useAsync } from '../hooks/useAsync'

function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

const DESDE_INICIAL = restarDias(FECHA_CORTE, 6)

type Copia = 'ninguna' | 'copiado' | 'error'

export default function Parte() {
  const estaciones = useAsync((signal) => getStations({ limit: 200 }, signal), [])
  const [elegidas, setElegidas] = useState<number[]>([])
  const [desde, setDesde] = useState(DESDE_INICIAL)
  const [hasta, setHasta] = useState(FECHA_CORTE)
  const [parte, setParte] = useState<Report | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copia, setCopia] = useState<Copia>('ninguna')

  const rangoValido = desde !== '' && hasta !== '' && desde <= hasta && hasta <= FECHA_CORTE
  const puedeGenerar = elegidas.length > 0 && rangoValido && !cargando

  function alternar(id: number) {
    setElegidas((actuales) =>
      actuales.includes(id)
        ? actuales.filter((x) => x !== id)
        : actuales.length < MAX_ESTACIONES_PARTE
          ? [...actuales, id]
          : actuales,
    )
  }

  async function generar(evento: FormEvent) {
    evento.preventDefault()
    if (!puedeGenerar) return
    setCargando(true)
    setError(null)
    setCopia('ninguna')
    try {
      setParte(await getReport({ stationIds: elegidas, from: desde, to: hasta }))
    } catch (e) {
      setParte(null)
      setError(e instanceof ApiError ? e.message : 'Ocurrió un error inesperado.')
    } finally {
      setCargando(false)
    }
  }

  async function copiar() {
    if (!parte) return
    try {
      await navigator.clipboard.writeText(parte.text)
      setCopia('copiado')
    } catch {
      setCopia('error')
    }
  }

  return (
    <section>
      <div className="no-imprimir">
        <h2>Parte pluvial</h2>
        <p>
          Elegí las estaciones y el período. El parte indica la fuente, la categoría, la fecha de
          corte y las advertencias de calidad. Un día sin dato no cuenta como 0 mm.
        </p>

        <form className="filtros" onSubmit={(e) => void generar(e)}>
          <fieldset className="estaciones-lista">
            <legend>Estaciones (hasta {MAX_ESTACIONES_PARTE})</legend>
            {estaciones.estado.tipo === 'cargando' && <Cargando />}
            {estaciones.estado.tipo === 'error' && (
              <ErrorEstado
                mensaje={estaciones.estado.mensaje}
                onReintentar={estaciones.reintentar}
              />
            )}
            {estaciones.estado.tipo === 'listo' &&
              (estaciones.estado.datos.items.length === 0 ? (
                <Vacio>No hay estaciones cargadas.</Vacio>
              ) : (
                estaciones.estado.datos.items.map((s) => (
                  <label key={s.id} className="opcion">
                    <input
                      type="checkbox"
                      checked={elegidas.includes(s.id)}
                      onChange={() => alternar(s.id)}
                    />
                    {s.name} ({s.code})
                  </label>
                ))
              ))}
          </fieldset>
          <label>
            Desde
            <input
              type="date"
              value={desde}
              max={FECHA_CORTE}
              onChange={(e) => setDesde(e.target.value)}
            />
          </label>
          <label>
            Hasta
            <input
              type="date"
              value={hasta}
              max={FECHA_CORTE}
              onChange={(e) => setHasta(e.target.value)}
            />
          </label>
          <div className="acciones">
            <button type="submit" disabled={!puedeGenerar}>
              Generar parte
            </button>
          </div>
        </form>

        {!rangoValido && (
          <ErrorEstado
            mensaje={`Elegí un período válido: «Desde» no puede ser posterior a «Hasta» y ninguna fecha puede pasar del ${FECHA_CORTE}.`}
          />
        )}
        {cargando && <Cargando texto="Armando el parte…" />}
        {error && <ErrorEstado mensaje={error} />}
      </div>

      {parte && (
        <article className="parte" aria-label="Parte pluvial">
          <div className="no-imprimir acciones">
            <button type="button" onClick={() => void copiar()}>
              Copiar texto
            </button>
            <button type="button" onClick={() => window.print()}>
              Imprimir
            </button>
          </div>
          <p role="status" className="nota no-imprimir">
            {copia === 'copiado' && 'Texto copiado. Ya lo podés pegar.'}
            {copia === 'error' &&
              'No se pudo copiar automáticamente: seleccioná el texto del parte y copialo.'}
          </p>
          <pre className="parte-texto">{parte.text}</pre>

          {parte.comparability_warnings.length > 0 && (
            <ul className="advertencias no-imprimir">
              {parte.comparability_warnings.map((w) => (
                <li key={w.code}>
                  <InsigniaAdvertencia codigo={w.code} mensaje={w.message} />
                </li>
              ))}
            </ul>
          )}
          {parte.not_evaluated.length > 0 && (
            <details className="no-imprimir">
              <summary>Advertencias que no se pudieron evaluar</summary>
              <ul>
                {parte.not_evaluated.map((n) => (
                  <li key={n.code}>{n.reason}</li>
                ))}
              </ul>
            </details>
          )}
        </article>
      )}
    </section>
  )
}
