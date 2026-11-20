import { useMemo } from 'react'
import type { Feature, FeatureCollection } from 'geojson'
import type { AccumulatedStation, NetworkState, Station } from '../../api/types'
import { colorMm, textoMmMapa } from '../../pages/map-helpers'
import {
  alturaBloque,
  ALTURA_BASE,
  ALTURA_MAXIMA,
  estadoDePieza,
  normalizar,
  textoDepartamento,
  type ResumenDepto,
} from './maqueta-datos'
import { caminoDe, caminoLineas, centroDe, crearProyeccion } from './proyeccion'

const PASO_PARED = 2 // cada cuántas unidades se apila una capa de pared al extruir el bloque

interface Props {
  departamentos: FeatureCollection
  estaciones: Station[]
  acumulados: Map<number, AccumulatedStation>
  salud: Map<number, NetworkState>
  resumen: Map<string, ResumenDepto>
  seleccionado: string | null
  /** Cursos de agua perennes e intermitentes del IGN; null si no cargaron (no es un error). */
  rios?: FeatureCollection | null
  intermitentes?: FeatureCollection | null
  mostrarIntermitentes?: boolean
  exageracion?: number
  onSeleccionar: (nombre: string) => void
}

function nombreDe(f: Feature): string {
  const n = (f.properties as { nombre?: unknown } | null)?.nombre
  return typeof n === 'string' ? n : 'Departamento'
}

export default function MaquetaSvg({
  departamentos,
  estaciones,
  acumulados,
  salud,
  resumen,
  seleccionado,
  rios = null,
  intermitentes = null,
  mostrarIntermitentes = false,
  exageracion = 1,
  onSeleccionar,
}: Props) {
  const proy = useMemo(() => crearProyeccion(departamentos, 28), [departamentos])
  const bloques = useMemo(
    () =>
      departamentos.features
        .map((f, i) => ({
          id: `maq-d-${i}`,
          nombre: nombreDe(f),
          d: caminoDe(f, proy),
          centro: centroDe(f, proy),
        }))
        // De atrás hacia adelante: el bloque de adelante tapa la pared del que tiene detrás.
        .sort((a, b) => a.centro.y - b.centro.y),
    [departamentos, proy],
  )
  const dRios = useMemo(() => (rios ? caminoLineas(rios, proy) : ''), [rios, proy])
  const dInt = useMemo(
    () => (intermitentes && mostrarIntermitentes ? caminoLineas(intermitentes, proy) : ''),
    [intermitentes, mostrarIntermitentes, proy],
  )
  const alturas = new Map(
    bloques.map((b) => {
      const r = resumen.get(normalizar(b.nombre))
      return [b.nombre, alturaBloque(r?.maximoMm ?? null, exageracion)] as const
    }),
  )
  const suelo = (ALTURA_BASE + ALTURA_MAXIMA) * exageracion
  const piezas = estaciones.filter((s) => s.lat != null && s.lon != null)

  return (
    <svg
      className="maqueta-svg"
      viewBox={`0 0 ${proy.ancho.toFixed(0)} ${(proy.alto + suelo).toFixed(0)}`}
      role="group"
      aria-label="Maqueta 3D de Formosa por departamentos: la altura repite el acumulado"
    >
      <defs>
        <pattern id="maqueta-rayas" width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="6" fill="#eceff1" />
          <path d="M0 6 L6 0" stroke="#78909c" strokeWidth="1" />
        </pattern>
        {bloques.map((b) => (
          <path key={b.id} id={b.id} d={b.d} />
        ))}
        {bloques.map((b) => (
          <clipPath key={`c-${b.id}`} id={`c-${b.id}`}>
            <use href={`#${b.id}`} />
          </clipPath>
        ))}
        {dRios && (
          <>
            <path id="maq-rio-borde" d={dRios} className="maqueta-rio-borde" />
            <path id="maq-rio" d={dRios} className="maqueta-rio" />
          </>
        )}
        {dInt && <path id="maq-rio-int" d={dInt} className="maqueta-rio-int" />}
      </defs>
      <g transform={`translate(0 ${suelo})`}>
        {bloques.map((b) => {
          const r = resumen.get(normalizar(b.nombre))
          const sinDato = !r || r.maximoMm === null
          const color = sinDato ? 'url(#maqueta-rayas)' : colorMm(r.maximoMm)
          const pared = sinDato ? '#90a4ae' : colorMm(r.maximoMm)
          const alto = alturas.get(b.nombre) ?? 0
          const activo = seleccionado === b.nombre
          const capas = Math.ceil(alto / PASO_PARED)
          return (
            <g
              key={b.nombre}
              className={`maqueta-bloque${activo ? ' maqueta-bloque-activo' : ''}`}
              role="button"
              tabIndex={0}
              aria-pressed={activo}
              aria-label={textoDepartamento(b.nombre, r)}
              onClick={() => onSeleccionar(b.nombre)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSeleccionar(b.nombre)
                }
              }}
            >
              <g aria-hidden="true" className="maqueta-pared" fill={pared}>
                {Array.from({ length: capas }, (_, k) => (
                  <use key={k} href={`#${b.id}`} y={-k * PASO_PARED} />
                ))}
              </g>
              <g transform={`translate(0 ${-alto})`}>
                <use href={`#${b.id}`} fill={color} className="maqueta-tapa" />
                {dRios && (
                  <g clipPath={`url(#c-${b.id})`} aria-hidden="true" pointerEvents="none">
                    <use href="#maq-rio-borde" />
                    <use href="#maq-rio" />
                    {dInt && <use href="#maq-rio-int" />}
                  </g>
                )}
                <text x={b.centro.x} y={b.centro.y} className="maqueta-nombre" aria-hidden="true">
                  {b.nombre}
                </text>
              </g>
            </g>
          )
        })}
        {piezas.map((s) => {
          const p = proy.proyectar(s.lon as number, s.lat as number)
          const estado = estadoDePieza(acumulados.get(s.id), salud.get(s.id))
          const mm = acumulados.get(s.id)?.accumulated_mm ?? null
          const alto = s.department
            ? (alturas.get(nombreEnCatalogo(bloques, s.department)) ?? 0)
            : 0
          return (
            <g
              key={s.id}
              className={`maqueta-pieza maqueta-pieza-${estado}`}
              transform={`translate(${p.x.toFixed(1)} ${(p.y - alto).toFixed(1)})`}
            >
              <title>
                {`${s.name}: ${
                  estado === 'en_silencio'
                    ? 'en silencio'
                    : estado === 'sin_dato'
                      ? 'sin dato'
                      : textoMmMapa(mm)
                }`}
              </title>
              <ellipse cx="0" cy="0" rx="5" ry="2.5" className="maqueta-pieza-base" />
              <rect
                x="-5"
                y="-9"
                width="10"
                height="9"
                fill={estado === 'con_dato' ? colorMm(mm) : '#cfd8dc'}
              />
              <ellipse
                cx="0"
                cy="-9"
                rx="5"
                ry="2.5"
                fill={estado === 'con_dato' ? colorMm(mm) : '#eceff1'}
              />
            </g>
          )
        })}
      </g>
    </svg>
  )
}

/** Nombre del bloque que corresponde al departamento de una estación (sin tildes ni mayúsculas). */
function nombreEnCatalogo(bloques: { nombre: string }[], departamento: string): string {
  const clave = normalizar(departamento)
  return bloques.find((b) => normalizar(b.nombre) === clave)?.nombre ?? ''
}
