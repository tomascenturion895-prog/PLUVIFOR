import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Day } from '../api/types'
import { textoMm } from './insignias-datos'
import { armarPuntos, type Punto } from './serie-diaria-datos'

function Detalle({ active, payload }: { active?: boolean; payload?: { payload: Punto }[] }) {
  const punto = active ? payload?.[0]?.payload : undefined
  if (!punto) return null
  return (
    <div className="grafico-detalle">
      <strong>{punto.fecha}</strong>
      <div>{punto.estado === 'dato' ? textoMm(punto.mm) : 'Sin dato'}</div>
    </div>
  )
}

export default function SerieDiaria({ days }: { days: Day[] }) {
  const puntos = armarPuntos(days)
  return (
    <figure className="grafico">
      <figcaption>
        Lluvia diaria (mm). Las franjas grises rayadas son días <strong>sin dato</strong>: no
        significan 0 mm.
      </figcaption>
      <div className="grafico-area" role="img" aria-label="Gráfico de barras de la lluvia diaria">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={puntos} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <pattern id="rayas" width="6" height="6" patternUnits="userSpaceOnUse">
                <rect width="6" height="6" fill="#eef0f2" />
                <path d="M0 6 L6 0" stroke="#8a949e" strokeWidth="1" />
              </pattern>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="fecha" minTickGap={32} tick={{ fontSize: 11 }} />
            <YAxis width={36} tick={{ fontSize: 11 }} />
            <Tooltip content={<Detalle />} />
            <Bar dataKey="mm" stackId="d" fill="#0284c7" isAnimationActive={false} />
            <Bar dataKey="hueco" stackId="d" fill="url(#rayas)" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
