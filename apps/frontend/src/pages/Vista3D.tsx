import { useMemo, useState } from 'react'
import type { FeatureCollection } from 'geojson'
import { Link } from 'react-router-dom'
import { ApiError, getRainfall, getStations } from '../api/client'
import type { Station } from '../api/types'
import { Cargando, ErrorEstado } from '../components/Estados'
import { InsigniaCategoria } from '../components/Insignias'
import {
  COLOR_CLASE,
  TEXTO_CLASE,
  UMBRAL_EVENTO_FUERTE_MM,
  UMBRAL_EVENTO_MM,
  armarDepartamentos,
  clasePluvial,
  leerSerie,
  redHidrica,
  ubicarEstacion,
  type Clase,
  type Departamento,
  type LecturaEstacion,
} from '../components/vista3d/exposicion-datos'
import ProvinciaEscena from '../components/vista3d/ProvinciaEscena'
import { COLOR_HIDRICA, type Modo, type PinEstacion } from '../components/vista3d/provincia-aspecto'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'
import type { ClaveTraduccion } from '../i18n/traducciones/es'

const DEPARTAMENTOS = '/geo/formosa_departamentos.geojson'
const PERENNES = '/geo/formosa_cursos_agua_perennes.geojson'
const INTERMITENTES = '/geo/formosa_cursos_agua_intermitentes.geojson'

async function cargarCapa(url: string, signal: AbortSignal, obligatoria: boolean) {
  try {
    const r = await fetch(url, { signal })
    if (!r.ok) throw new Error()
    const v = (await r.json()) as { type?: unknown; features?: unknown }
    if (v.type !== 'FeatureCollection' || !Array.isArray(v.features)) throw new Error()
    return v as FeatureCollection
  } catch (e) {
    if (signal.aborted) throw e
    if (obligatoria)
      throw new ApiError(0, 'geo_error', 'No se pudo cargar el mapa de departamentos.')
    return null
  }
}

async function cargarCapas(signal: AbortSignal) {
  const [deptos, perennes, intermitentes] = await Promise.all([
    cargarCapa(DEPARTAMENTOS, signal, true),
    cargarCapa(PERENNES, signal, false),
    cargarCapa(INTERMITENTES, signal, false),
  ])
  return { deptos: deptos!, perennes, intermitentes }
}

interface Periodo {
  desde: string
  hasta: string
}

const PERIODOS: { id: string; clave: ClaveTraduccion; periodo: Periodo }[] = [
  { id: 'nino', clave: 'v3d.periodo.nino', periodo: { desde: '2015-09-01', hasta: '2016-06-30' } },
  { id: 'caso', clave: 'v3d.periodo.caso', periodo: { desde: '2015-09-20', hasta: '2016-06-26' } },
  {
    id: 'registro',
    clave: 'v3d.periodo.registro',
    periodo: { desde: '1960-01-01', hasta: FECHA_CORTE },
  },
]

const CLAVE_CLASE: Record<Clase, ClaveTraduccion> = {
  baja: 'v3d.clase.baja',
  media: 'v3d.clase.media',
  alta: 'v3d.clase.alta',
}

/** Estaciones activas en el período (las demás no pueden tener datos). */
function activasEn(estaciones: Station[], p: Periodo): Station[] {
  return estaciones.filter(
    (s) => (!s.active_from || s.active_from <= p.hasta) && (!s.active_to || s.active_to >= p.desde),
  )
}

async function cargarLecturas(estaciones: Station[], p: Periodo, signal: AbortSignal) {
  const series = await Promise.all(
    activasEn(estaciones, p)
      .slice(0, 20)
      .map((s) =>
        getRainfall(
          { stationId: s.id, from: p.desde, to: p.hasta, category: 'observado' },
          signal,
        ).then(
          (serie) => ({ serie, s }),
          (e: unknown) => {
            if (signal.aborted) throw e
            return null
          },
        ),
      ),
  )
  const lecturas = new Map<number, LecturaEstacion>()
  const diaMayor = new Map<number, { fecha: string; mm: number }>()
  for (const r of series) {
    if (!r) continue
    lecturas.set(r.s.id, leerSerie(r.serie))
    for (const d of r.serie.days) {
      if (d.state !== 'dato' || d.mm === null) continue
      const actual = diaMayor.get(r.s.id)
      if (!actual || d.mm > actual.mm) diaMayor.set(r.s.id, { fecha: d.obs_date, mm: d.mm })
    }
  }
  return { lecturas, diaMayor }
}

const mm = (v: number) => `${v.toLocaleString('es-AR', { maximumFractionDigits: 1 })} mm`
const fecha = (iso: string) => iso.split('-').reverse().join('/')

function Muestra({ color }: { color: string | null }) {
  return (
    <span
      className={`v3d-muestra${color ? '' : ' v3d-muestra-sin-dato'}`}
      style={color ? { background: color } : undefined}
      aria-hidden="true"
    />
  )
}

function textoPluvial(d: Departamento): string {
  if (d.pluvial) return TEXTO_CLASE[d.pluvial]
  if (d.lecturas.some((l) => l.descarte === 'racha_de_ceros')) return 'Sin dato confiable'
  return 'Sin dato'
}

function DetalleDepartamento({ d }: { d: Departamento }) {
  return (
    <div className="v3d-detalle">
      <h3>{d.nombre}</h3>
      <dl>
        <div>
          <dt>Exposición estimada</dt>
          <dd>
            <Muestra color={d.exposicion ? COLOR_CLASE[d.exposicion] : null} />
            {d.exposicion ? TEXTO_CLASE[d.exposicion] : 'Sin dato'}
          </dd>
        </div>
        <div>
          <dt>Lluvia (días ≥ 50 y ≥ 100 mm)</dt>
          <dd>
            <Muestra color={d.pluvial ? COLOR_CLASE[d.pluvial] : null} />
            {textoPluvial(d)}
          </dd>
        </div>
        <div>
          <dt>Red hídrica</dt>
          <dd>
            <Muestra color={d.hidrica ? COLOR_HIDRICA[d.hidrica.clase] : null} />
            {d.hidrica
              ? `${TEXTO_CLASE[d.hidrica.clase]} · ${d.hidrica.densidad.toLocaleString('es-AR', { maximumFractionDigits: 1 })} km cada 100 km²`
              : 'Sin dato'}
          </dd>
        </div>
      </dl>
      {d.lecturas.length > 0 ? (
        <ul className="v3d-estaciones">
          {d.lecturas.map((l) => (
            <li key={l.estacionId}>
              <strong>{l.nombre}</strong>
              {l.descarte === 'racha_de_ceros' ? (
                <span className="v3d-descartada">
                  Descartada: racha de ceros de 60 días o más. Puede ser un sensor sin registrar.
                </span>
              ) : l.maximoDiarioMm === null ? (
                <span>Sin días con dato en el período.</span>
              ) : (
                <span>
                  Mayor día: {mm(l.maximoDiarioMm)} · {l.diasSobre50} días ≥ {UMBRAL_EVENTO_MM} mm ·{' '}
                  {l.diasSobre100} ≥ {UMBRAL_EVENTO_FUERTE_MM} mm · {l.diasConDato} días con dato
                </span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="v3d-nota">No hay estaciones con datos de lluvia en este departamento.</p>
      )}
      {d.deducidas.length > 0 && (
        <p className="v3d-nota">
          Departamento asignado por la ubicación verificada de: {d.deducidas.join(', ')}.
        </p>
      )}
    </div>
  )
}

const MODOS: { id: Modo; clave: ClaveTraduccion }[] = [
  { id: 'exposicion', clave: 'v3d.modo.exposicion' },
  { id: 'pluvial', clave: 'v3d.modo.pluvial' },
  { id: 'hidrica', clave: 'v3d.modo.hidrica' },
]

function LeyendaProvincia({ modo }: { modo: Modo }) {
  const { t } = useIdioma()
  const colores = modo === 'hidrica' ? COLOR_HIDRICA : COLOR_CLASE
  const titulo =
    modo === 'exposicion'
      ? t('v3d.leyenda.exposicion')
      : modo === 'pluvial'
        ? `${t('v3d.modo.pluvial')}: ≥ ${UMBRAL_EVENTO_MM} / ≥ ${UMBRAL_EVENTO_FUERTE_MM} mm`
        : t('v3d.leyenda.hidrica')
  return (
    <div className="v3d-leyenda">
      <p className="v3d-leyenda-titulo">{titulo}</p>
      <ul>
        {(['baja', 'media', 'alta'] as Clase[]).map((c) => (
          <li key={c}>
            <Muestra color={colores[c]} />
            {modo === 'pluvial'
              ? c === 'alta'
                ? `≥ ${UMBRAL_EVENTO_FUERTE_MM} mm`
                : c === 'media'
                  ? `≥ ${UMBRAL_EVENTO_MM} mm`
                  : `< ${UMBRAL_EVENTO_MM} mm`
              : t(CLAVE_CLASE[c])}
          </li>
        ))}
        <li>
          <Muestra color={null} />
          {t('v3d.leyenda.sinDato')}
        </li>
        <li>
          <span className="v3d-muestra-rio" aria-hidden="true" />
          {t('v3d.leyenda.rios')}
        </li>
      </ul>
      <p className="v3d-nota">{t('v3d.leyenda.altura')}</p>
    </div>
  )
}

function Provincia({
  capas,
  estaciones,
  periodo,
}: {
  capas: Awaited<ReturnType<typeof cargarCapas>>
  estaciones: Station[]
  periodo: Periodo
}) {
  const { t } = useIdioma()
  const [modo, setModo] = useState<Modo>('exposicion')
  const [elegido, setElegido] = useState<string | null>(null)
  const [sinWebGL, setSinWebGL] = useState(false)
  const lecturas = useAsync(
    (signal) => cargarLecturas(estaciones, periodo, signal),
    [estaciones, periodo.desde, periodo.hasta],
  )
  const hidrica = useMemo(
    () => redHidrica(capas.deptos, capas.perennes, capas.intermitentes),
    [capas],
  )
  const datos = useMemo(
    () =>
      armarDepartamentos(
        capas.deptos,
        hidrica,
        estaciones,
        lecturas.estado.tipo === 'listo' ? lecturas.estado.datos.lecturas : new Map(),
      ),
    [capas.deptos, hidrica, estaciones, lecturas.estado],
  )
  const pines = useMemo<PinEstacion[]>(() => {
    const leidas = lecturas.estado.tipo === 'listo' ? lecturas.estado.datos.lecturas : new Map()
    return estaciones
      .filter((s) => s.lat != null && s.lon != null && s.coords_status === 'verificada')
      .map((s) => {
        const l = leidas.get(s.id) as LecturaEstacion | undefined
        return {
          id: s.id,
          nombre: s.name.split(' - ')[0],
          lon: s.lon!,
          lat: s.lat!,
          clase: l ? clasePluvial(l) : null,
          descartada: l?.descarte === 'racha_de_ceros',
        }
      })
  }, [estaciones, lecturas.estado])
  const seleccion = datos.find((d) => d.clave === elegido) ?? null
  const conExposicion = datos.filter((d) => d.exposicion).length

  return (
    <div className="v3d-vista">
      <div className="v3d-escenario">
        {sinWebGL ? (
          <p className="v3d-sin-webgl">{t('v3d.sinWebgl')}</p>
        ) : (
          <ProvinciaEscena
            deptos={capas.deptos}
            datos={datos}
            perennes={capas.perennes}
            intermitentes={capas.intermitentes}
            estaciones={pines}
            modo={modo}
            seleccionado={elegido}
            onSeleccionar={setElegido}
            onSinWebGL={() => setSinWebGL(true)}
          />
        )}
        <div className="v3d-panel v3d-panel-arriba-izq">
          <div className="v3d-segmentado" role="radiogroup" aria-label={t('v3d.modoAria')}>
            {MODOS.map((m) => (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={modo === m.id}
                className={modo === m.id ? 'es-activo' : ''}
                onClick={() => setModo(m.id)}
              >
                {t(m.clave)}
              </button>
            ))}
          </div>
          <p className="v3d-ayuda-gesto">{t('v3d.gesto')}</p>
        </div>
        <div className="v3d-panel v3d-panel-abajo-izq">
          <LeyendaProvincia modo={modo} />
        </div>
        <aside className="v3d-panel v3d-panel-der" aria-live="polite">
          <div className="v3d-insignias">
            <InsigniaCategoria categoria="estimado" />
          </div>
          {lecturas.estado.tipo === 'cargando' && <Cargando texto={t('v3d.leyendo')} />}
          {lecturas.estado.tipo === 'error' && (
            <ErrorEstado mensaje={lecturas.estado.mensaje} onReintentar={lecturas.reintentar} />
          )}
          {seleccion ? (
            <DetalleDepartamento d={seleccion} />
          ) : (
            <div className="v3d-detalle">
              <h3>{t('v3d.resumenTitulo')}</h3>
              <p>
                {conExposicion} {t('comun.de')} {datos.length} — {t('v3d.leyenda.exposicion')}.
              </p>
              <p className="v3d-nota">{t('v3d.elegirDepto')}</p>
            </div>
          )}
        </aside>
      </div>

      <section className="v3d-tabla-caja" aria-labelledby="v3d-tabla-titulo">
        <h3 id="v3d-tabla-titulo">{t('v3d.departamentos')}</h3>
        <div className="tabla-scroll">
          <table className="v3d-tabla">
            <thead>
              <tr>
                <th scope="col">{t('v3d.departamento')}</th>
                <th scope="col">{t('v3d.modo.exposicion')}</th>
                <th scope="col">{t('v3d.modo.pluvial')}</th>
                <th scope="col">{t('v3d.modo.hidrica')} (km / 100 km²)</th>
              </tr>
            </thead>
            <tbody>
              {[...datos]
                .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
                .map((d) => (
                  <tr key={d.clave} className={d.clave === elegido ? 'es-elegida' : ''}>
                    <th scope="row">
                      <button
                        type="button"
                        className="v3d-enlace"
                        aria-pressed={d.clave === elegido}
                        onClick={() => setElegido(d.clave === elegido ? null : d.clave)}
                      >
                        {d.nombre}
                      </button>
                    </th>
                    <td>
                      <Muestra color={d.exposicion ? COLOR_CLASE[d.exposicion] : null} />
                      {d.exposicion ? TEXTO_CLASE[d.exposicion] : 'Sin dato'}
                    </td>
                    <td>{textoPluvial(d)}</td>
                    <td className="num">
                      {d.hidrica
                        ? `${d.hidrica.densidad.toLocaleString('es-AR', { maximumFractionDigits: 1 })} · ${TEXTO_CLASE[d.hidrica.clase]}`
                        : 'Sin dato'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <details className="v3d-metodo">
          <summary>Cómo se calcula</summary>
          <ul>
            <li>
              <strong>Lluvia (observado, SIGA/INTA):</strong> alta si alguna estación del
              departamento tuvo un día de {UMBRAL_EVENTO_FUERTE_MM} mm o más; media si tuvo uno de{' '}
              {UMBRAL_EVENTO_MM} mm o más; baja si no. Se toma la estación más lluviosa: los
              milímetros de estaciones distintas no se suman ni se promedian. Los días sin dato no
              cuentan como 0 mm y una estación con racha de ceros se descarta.
            </li>
            <li>
              <strong>Red hídrica (referencia cartográfica, IGN):</strong> kilómetros de cursos de
              agua perennes e intermitentes por cada 100 km², repartidos en tercios entre los 9
              departamentos. Es aproximada: las capas están simplificadas.
            </li>
            <li>
              <strong>Exposición (estimado):</strong> cruza las dos en una tabla de 3 × 3. Sin dato
              de lluvia no hay exposición. No es una predicción de inundación ni un mapa de riesgo
              oficial: falta el relieve, el suelo y el estado de los ríos.
            </li>
          </ul>
        </details>
      </section>
    </div>
  )
}

export default function Vista3D() {
  const { t } = useIdioma()
  const [periodoId, setPeriodoId] = useState('nino')
  const periodo = PERIODOS.find((p) => p.id === periodoId)!.periodo
  const capas = useAsync(cargarCapas, [])
  const catalogo = useAsync((signal) => getStations({ limit: 200 }, signal), [])
  const estaciones = useMemo(
    () => (catalogo.estado.tipo === 'listo' ? catalogo.estado.datos.items : []),
    [catalogo.estado],
  )
  const deptos = capas.estado.tipo === 'listo' ? capas.estado.datos.deptos : null
  const ubicadas = useMemo(
    () => (deptos ? estaciones.filter((s) => ubicarEstacion(s, deptos).departamento).length : 0),
    [deptos, estaciones],
  )

  return (
    <section className="v3d" aria-labelledby="v3d-titulo">
      <header className="v3d-cabecera">
        <div>
          <h2 id="v3d-titulo">{t('nav.vista3d')}</h2>
          <p>{t('v3d.intro')}</p>
        </div>
      </header>

      <div className="v3d-periodos" role="group" aria-label={t('v3d.periodoAria')}>
        <span className="v3d-periodos-titulo">{t('v3d.lluviaDe')}</span>
        {PERIODOS.map((p) => (
          <button
            key={p.id}
            type="button"
            aria-pressed={p.id === periodoId}
            onClick={() => setPeriodoId(p.id)}
          >
            {t(p.clave)}
            <small>
              {fecha(p.periodo.desde)} – {fecha(p.periodo.hasta)}
            </small>
          </button>
        ))}
        {catalogo.estado.tipo === 'listo' && (
          <span className="v3d-periodos-nota">
            {estaciones.length} {t('comun.estaciones').toLowerCase()}, {ubicadas}{' '}
            {t(ubicadas === 1 ? 'v3d.departamento' : 'v3d.departamentos').toLowerCase()}.{' '}
            {fecha(FECHA_CORTE)}.
          </span>
        )}
      </div>

      {(capas.estado.tipo === 'cargando' || catalogo.estado.tipo === 'cargando') && (
        <Cargando texto={t('v3d.preparando')} />
      )}
      {capas.estado.tipo === 'error' && (
        <ErrorEstado mensaje={capas.estado.mensaje} onReintentar={capas.reintentar} />
      )}
      {catalogo.estado.tipo === 'error' && (
        <ErrorEstado mensaje={catalogo.estado.mensaje} onReintentar={catalogo.reintentar} />
      )}
      {capas.estado.tipo === 'listo' && catalogo.estado.tipo === 'listo' && (
        <Provincia capas={capas.estado.datos} estaciones={estaciones} periodo={periodo} />
      )}
      <p className="v3d-pie">
        {t('v3d.fuentesPie')}
        <Link to="/ayuda">{t('nav.ayuda')}</Link>.
      </p>
    </section>
  )
}
