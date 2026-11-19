import { useMemo } from 'react'
import type { Feature, FeatureCollection } from 'geojson'
import type { AccumulatedStation, NetworkState, Station } from '../../api/types'
import { colorMm, textoMmMapa } from '../../pages/map-helpers'
import { estadoDePieza, normalizar, textoDepartamento, type ResumenDepto } from './maqueta-datos'
import { caminoDe, centroDe, crearProyeccion } from './proyeccion'

const ALTURA = 10 // altura fija de los bloques: la altura no representa lluvia

interface Props {
  departamentos: FeatureCollection
  estaciones: Station[]
  acumulados: Map<number, AccumulatedStation>
  salud: Map<number, NetworkState>
  resumen: Map<string, ResumenDepto>
  seleccionado: string | null
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
  onSeleccionar,
}: Props) {
  const proy = useMemo(() => crearProyeccion(departamentos, 28), [departamentos])
  const bloques = useMemo(
    () =>
      departamentos.features.map((f) => ({
        nombre: nombreDe(f),
        d: caminoDe(f, proy),
        centro: centroDe(f, proy),
      })),
    [departamentos, proy],
  )
  const piezas = estaciones.filter((s) => s.lat != null && s.lon != null)

  return (
    <svg
      className="maqueta-svg"
      viewBox={`0 0 ${proy.ancho.toFixed(0)} ${(proy.alto + ALTURA).toFixed(0)}`}
      role="group"
      aria-label="Maqueta isométrica de Formosa por departamentos"
    >
      <defs>
        <pattern id="maqueta-rayas" width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="6" fill="#eceff1" />
          <path d="M0 6 L6 0" stroke="#78909c" strokeWidth="1" />
        </pattern>
      </defs>
      <g aria-hidden="true">
        {bloques.map((b) => (
          <path
            key={b.nombre}
            d={b.d}
            transform={`translate(0 ${ALTURA})`}
            className="maqueta-lado"
          />
        ))}
      </g>
      {bloques.map((b) => {
        const r = resumen.get(normalizar(b.nombre))
        const sinDato = !r || r.maximoMm === null
        const color = sinDato ? 'url(#maqueta-rayas)' : colorMm(r.maximoMm)
        const activo = seleccionado === b.nombre
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
            <path d={b.d} fill={color} className="maqueta-tapa" />
            <text x={b.centro.x} y={b.centro.y} className="maqueta-nombre" aria-hidden="true">
              {b.nombre}
            </text>
          </g>
        )
      })}
      {piezas.map((s) => {
        const p = proy.proyectar(s.lon as number, s.lat as number)
        const estado = estadoDePieza(acumulados.get(s.id), salud.get(s.id))
        const mm = acumulados.get(s.id)?.accumulated_mm ?? null
        return (
          <g
            key={s.id}
            className={`maqueta-pieza maqueta-pieza-${estado}`}
            transform={`translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})`}
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
    </svg>
  )
}
