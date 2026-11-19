import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FeatureCollection } from 'geojson'
import { ApiError, getAccumulated, getNetworkHealth, getStations } from '../api/client'
import type { AccumulatedOut, AccumulatedStation, NetworkState, Station } from '../api/types'
import { Cargando, ErrorEstado } from '../components/Estados'
import { InsigniaAdvertencia } from '../components/Insignias'
import MaquetaSvg from '../components/maqueta/MaquetaSvg'
import {
  normalizar,
  periodoAnterior,
  resumenPorDepartamento,
  ultimosDias,
} from '../components/maqueta/maqueta-datos'
import Atajos from '../components/shortcuts/Atajos'
import { resolverEstaciones, type Atajo } from '../components/shortcuts/atajos'
import BarraTiempo from '../components/timeline/BarraTiempo'
import { mesesDelPeriodo, type Mes } from '../components/timeline/timeline-datos'
import ProbaCambio, { type Variante } from '../components/panels/ProbaCambio'
import Resultados from '../components/panels/Resultados'
import { periodoValido, type SeleccionValor } from '../components/panels/panels-datos'
import Seleccion from '../components/panels/Seleccion'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { colorMm, textoMmMapa } from './map-helpers'

const DEPARTAMENTOS = '/geo/formosa_departamentos.geojson'

function hace(dias: number): string {
  return ultimosDias(FECHA_CORTE, dias).desde
}

async function cargarDepartamentos(signal: AbortSignal): Promise<FeatureCollection> {
  const respuesta = await fetch(DEPARTAMENTOS, { signal })
  if (!respuesta.ok)
    throw new ApiError(0, 'geo_error', 'No se pudo cargar el mapa de departamentos.')
  const valor: unknown = await respuesta.json()
  const col = valor as { type?: unknown; features?: unknown }
  if (col.type !== 'FeatureCollection' || !Array.isArray(col.features)) {
    throw new ApiError(0, 'geo_error', 'El mapa de departamentos no es válido.')
  }
  return valor as FeatureCollection
}

function mapaPorId(a: AccumulatedOut | null): Map<number, AccumulatedStation> {
  return new Map((a?.stations ?? []).map((s) => [s.station_id, s]))
}

function Leyenda() {
  const items = [
    { color: colorMm(0), etiqueta: '0 mm (dato real)' },
    { color: colorMm(5), etiqueta: '< 10 mm' },
    { color: colorMm(20), etiqueta: '10–30 mm' },
    { color: colorMm(45), etiqueta: '30–60 mm' },
    { color: colorMm(80), etiqueta: '60–100 mm' },
    { color: colorMm(120), etiqueta: '≥ 100 mm' },
  ]
  return (
    <ul className="mapa-leyenda" aria-label="Leyenda de la maqueta">
      {items.map((i) => (
        <li key={i.etiqueta} className="mapa-leyenda-item">
          <span className="mapa-leyenda-color" style={{ background: i.color }} aria-hidden="true" />
          {i.etiqueta}
        </li>
      ))}
      <li className="mapa-leyenda-item">
        <span className="mapa-leyenda-color mapa-leyenda-color-sin-dato" aria-hidden="true" />
        Sin dato (rayado): no es 0 mm
      </li>
      <li className="mapa-leyenda-item">
        <span aria-hidden="true">◐</span> Estación en silencio (apagada)
      </li>
    </ul>
  )
}

export default function Maqueta() {
  const geo = useAsync(cargarDepartamentos, [])
  const catalogo = useAsync((signal) => getStations({ limit: 200 }, signal), [])
  const [sel, setSel] = useState<SeleccionValor>({
    desde: hace(30),
    hasta: FECHA_CORTE,
    category: 'observado',
    zona: '',
    estaciones: [],
  })
  const [salud, setSalud] = useState<Map<number, NetworkState>>(new Map())
  const [variante, setVariante] = useState<Variante | null>(null)
  const [varDatos, setVarDatos] = useState<AccumulatedOut | null>(null)
  const [varCargando, setVarCargando] = useState(false)
  const [varError, setVarError] = useState<string | null>(null)
  const [atajo, setAtajo] = useState<Atajo['id'] | null>(null)
  const [meses, setMeses] = useState<Mes[] | null>(null)
  const [indiceMes, setIndiceMes] = useState(0)
  const [avisoAtajo, setAvisoAtajo] = useState<string | null>(null)
  const valido = periodoValido(sel)
  // En reproducción se pide un mes a la vez; si no, el período elegido entero.
  const periodo = meses ? meses[Math.min(indiceMes, meses.length - 1)] : sel

  const acumulado = useAsync(
    (signal) =>
      valido
        ? getAccumulated({ from: periodo.desde, to: periodo.hasta, category: sel.category }, signal)
        : Promise.resolve(null),
    [periodo.desde, periodo.hasta, sel.category, valido],
  )

  useEffect(() => {
    // El estado de silencio es un complemento: si falla, la maqueta sigue sin él.
    const c = new AbortController()
    getNetworkHealth({}, c.signal).then(
      (h) => setSalud(new Map(h.stations.map((s) => [s.station_id, s.state]))),
      () => setSalud(new Map()),
    )
    return () => c.abort()
  }, [])

  const estaciones: Station[] = useMemo(
    () => (catalogo.estado.tipo === 'listo' ? catalogo.estado.datos.items : []),
    [catalogo.estado],
  )
  const datos = acumulado.estado.tipo === 'listo' ? acumulado.estado.datos : null
  const acumulados = useMemo(() => mapaPorId(datos), [datos])
  const resumen = useMemo(
    () => resumenPorDepartamento(estaciones, acumulados),
    [estaciones, acumulados],
  )
  const departamentos = useMemo(
    () => [...new Set(estaciones.map((s) => s.department).filter((d): d is string => !!d))].sort(),
    [estaciones],
  )
  const elegidas = estaciones.filter(
    (s) =>
      (sel.zona === '' || s.department === sel.zona) &&
      (sel.estaciones.length === 0 || sel.estaciones.includes(s.id)),
  )

  function elegirDepartamento(nombre: string) {
    const real = departamentos.find((d) => normalizar(d) === normalizar(nombre)) ?? ''
    setSel((s) => ({ ...s, zona: s.zona === real ? '' : real, estaciones: [] }))
  }

  function elegirAtajo(a: Atajo) {
    const { ids, faltan } = resolverEstaciones(a.codigos, estaciones)
    if (faltan.length > 0) {
      setAvisoAtajo(
        `No se puede abrir este atajo: faltan en el catálogo las estaciones ${faltan.join(', ')}.`,
      )
      return
    }
    setAvisoAtajo(null)
    setAtajo(a.id)
    setSel({ desde: a.desde, hasta: a.hasta, category: 'observado', zona: '', estaciones: ids })
    setMeses(a.reproducir ? mesesDelPeriodo(a.desde, a.hasta, FECHA_CORTE) : null)
    setIndiceMes(0)
    setVariante(null)
    setVarDatos(null)
  }

  const cambiarMes = useCallback((i: number) => setIndiceMes(i), [])

  function cambiarSeleccion(v: SeleccionValor) {
    setAtajo(null)
    setMeses(null)
    setAvisoAtajo(null)
    setSel(v)
    setVariante(null)
    setVarDatos(null)
  }

  async function probar(v: Variante) {
    setVariante(v)
    setVarCargando(true)
    setVarError(null)
    try {
      setVarDatos(await getAccumulated({ from: v.desde, to: v.hasta, category: sel.category }))
    } catch (e) {
      setVarDatos(null)
      setVarError(e instanceof ApiError ? e.message : 'Ocurrió un error inesperado.')
    } finally {
      setVarCargando(false)
    }
  }

  function probarPeriodo(accion: 'anterior' | 'ultimos7' | 'ultimos30') {
    const p =
      accion === 'anterior'
        ? periodoAnterior(sel.desde, sel.hasta)
        : ultimosDias(sel.hasta, accion === 'ultimos7' ? 7 : 30)
    const etiqueta =
      accion === 'anterior'
        ? 'período anterior'
        : accion === 'ultimos7'
          ? 'últimos 7 días'
          : 'últimos 30 días'
    void probar({ ...p, extra: variante?.extra ?? null, etiqueta })
  }

  function sumarEstacion(id: number | null) {
    const base = variante ?? {
      desde: sel.desde,
      hasta: sel.hasta,
      extra: null,
      etiqueta: 'misma ventana',
    }
    void probar({
      ...base,
      extra: id,
      etiqueta: id === null ? base.etiqueta : 'con una estación más',
    })
  }

  const seleccionado = departamentos.find((d) => d === sel.zona) ?? null
  const detalle = seleccionado ? resumen.get(normalizar(seleccionado)) : undefined

  return (
    <section>
      <h2>Maqueta de Formosa</h2>
      <p>
        Tocá un departamento para ver su lluvia. El color es el{' '}
        <strong>mayor acumulado individual</strong> entre sus estaciones con dato; no es un total ni
        un promedio. Rayado = sin dato, que no es 0 mm.
      </p>
      {(geo.estado.tipo === 'cargando' || catalogo.estado.tipo === 'cargando') && <Cargando />}
      {geo.estado.tipo === 'error' && (
        <ErrorEstado mensaje={geo.estado.mensaje} onReintentar={geo.reintentar} />
      )}
      {catalogo.estado.tipo === 'error' && (
        <ErrorEstado mensaje={catalogo.estado.mensaje} onReintentar={catalogo.reintentar} />
      )}
      {acumulado.estado.tipo === 'error' && (
        <ErrorEstado mensaje={acumulado.estado.mensaje} onReintentar={acumulado.reintentar} />
      )}
      <Atajos activo={atajo} alElegir={elegirAtajo} />
      {avisoAtajo && <ErrorEstado mensaje={avisoAtajo} />}
      {meses && meses.length > 0 && (
        <BarraTiempo
          meses={meses}
          indice={indiceMes}
          cargando={acumulado.estado.tipo === 'cargando'}
          alCambiar={cambiarMes}
        />
      )}
      <div className="maqueta-layout">
        <div className="maqueta-escena">
          {geo.estado.tipo === 'listo' && (
            <MaquetaSvg
              departamentos={geo.estado.datos}
              estaciones={estaciones}
              acumulados={acumulados}
              salud={salud}
              resumen={resumen}
              seleccionado={seleccionado}
              onSeleccionar={elegirDepartamento}
            />
          )}
          <Leyenda />
          {seleccionado && (
            <section
              className="mapa-resumen-departamento"
              aria-label={`Detalle de ${seleccionado}`}
            >
              <h3>Departamento: {seleccionado}</h3>
              {!detalle || detalle.estaciones === 0 ? (
                <p className="nota">No hay estaciones de este departamento en el catálogo.</p>
              ) : (
                <>
                  <p>
                    Mayor acumulado individual: <strong>{textoMapa(detalle.maximoMm)}</strong> ·{' '}
                    {detalle.conDato} de {detalle.estaciones} estaciones con dato.
                  </p>
                  <ul>
                    {elegidas.map((s) => (
                      <li key={s.id}>
                        {s.name} — {textoMmMapa(acumulados.get(s.id)?.accumulated_mm)}
                        {acumulados.get(s.id)?.warnings.map((w) => (
                          <InsigniaAdvertencia key={w.code} codigo={w.code} mensaje={w.message} />
                        ))}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}
        </div>
        <div className="maqueta-paneles">
          <Seleccion
            valor={sel}
            estaciones={estaciones}
            departamentos={departamentos}
            onCambiar={cambiarSeleccion}
          />
          {datos && valido && (
            <Resultados datos={datos} estaciones={elegidas} acumulados={acumulados} />
          )}
          {datos && valido && (
            <ProbaCambio
              base={acumulados}
              idsBase={elegidas.map((s) => s.id)}
              variante={variante}
              varianteDatos={mapaVariante(varDatos)}
              cargando={varCargando}
              error={varError}
              candidatas={estaciones.filter((s) => !elegidas.some((e) => e.id === s.id))}
              estaciones={estaciones}
              onProbar={probarPeriodo}
              onSumar={sumarEstacion}
              onLimpiar={() => {
                setVariante(null)
                setVarDatos(null)
              }}
            />
          )}
        </div>
      </div>
    </section>
  )
}

function mapaVariante(a: AccumulatedOut | null): Map<number, AccumulatedStation> | null {
  return a ? mapaPorId(a) : null
}

function textoMapa(mm: number | null): string {
  return textoMmMapa(mm)
}
