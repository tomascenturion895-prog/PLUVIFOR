import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { armarPuntosSensor, type PuntoSensor } from '../../pages/sensores-datos'
import { formatoMm } from '../../pages/network-health-datos'
import type { SensorReading } from '../../api/types'
import { DALTONICO, esDaltonico } from '../tema/tema-colores'

function Detalle({ active, payload }: { active?: boolean; payload?: { payload: PuntoSensor }[] }) {
  const punto = active ? payload?.[0]?.payload : undefined
  if (!punto) return null
  return (
    <div className="grafico-detalle">
      <strong>{punto.etiqueta}</strong>
      <div>{punto.mm === null ? 'Sin lectura' : formatoMm(punto.mm)}</div>
    </div>
  )
}

/** Lluvia medida por un dispositivo simulado. Un día sin lectura es un hueco rayado, no 0 mm. */
export default function GraficoSensor({ lecturas }: { lecturas: SensorReading[] }) {
  const puntos = armarPuntosSensor(lecturas)
  return (
    <figure className="grafico">
      <figcaption>
        Lluvia medida por el dispositivo (mm), <strong>simulada</strong>. Las franjas grises rayadas
        son días <strong>sin lectura</strong>: no significan 0 mm.
      </figcaption>
      <div
        className="grafico-area"
        role="img"
        aria-label="Gráfico de barras de las lecturas simuladas del dispositivo"
      >
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={puntos} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <pattern id="rayas-sensor" width="6" height="6" patternUnits="userSpaceOnUse">
                <rect width="6" height="6" fill="#eef0f2" />
                <path d="M0 6 L6 0" stroke="#8a949e" strokeWidth="1" />
              </pattern>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="etiqueta" minTickGap={40} tick={{ fontSize: 11 }} />
            <YAxis width={36} tick={{ fontSize: 11 }} />
            <Tooltip content={<Detalle />} />
            <Bar
              dataKey="mm"
              stackId="d"
              fill={esDaltonico() ? DALTONICO.barras : '#0284c7'}
              isAnimationActive={false}
            />
            <Bar dataKey="hueco" stackId="d" fill="url(#rayas-sensor)" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
