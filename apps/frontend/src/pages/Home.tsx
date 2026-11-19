import { Link } from 'react-router-dom'

const ACCESOS = [
  {
    ruta: '/maqueta',
    nombre: 'Maqueta',
    texto: 'La provincia de un vistazo: tocá un departamento y mirá cuánto llovió.',
  },
  {
    ruta: '/mapa',
    nombre: 'Mapa',
    texto: 'Las estaciones sobre el mapa, con su acumulado del período.',
  },
  {
    ruta: '/comparador',
    nombre: 'Comparador',
    texto: 'Compará estaciones y períodos, con sus advertencias.',
  },
  {
    ruta: '/parte',
    nombre: 'Parte pluvial',
    texto: 'Un texto listo para copiar o imprimir, con la fuente y la calidad.',
  },
  {
    ruta: '/reporte',
    nombre: 'Reporte de campo',
    texto: 'Cargá la lluvia anotada donde no hay estación.',
  },
] as const

export default function Home() {
  return (
    <section>
      <div className="hero">
        <div className="hero-texto">
          <h2>¿Cuánto llovió, dónde y en qué período?</h2>
          <p>
            PLUVIFOR responde esa pregunta para la provincia de Formosa y siempre dice{' '}
            <strong>qué tan confiable es cada dato</strong>: de qué estación viene, si es medido o
            estimado y qué advertencias tiene.
          </p>
          <p>
            Un día sin dato se muestra como «sin dato», nunca como 0 mm: que falte la medición no
            significa que no haya llovido.
          </p>
        </div>
        <figure className="hero-figura">
          <svg
            viewBox="0 0 280 150"
            role="img"
            aria-label="Ilustración: barras de lluvia diaria; los días sin dato se dibujan rayados, no como cero."
          >
            <defs>
              <pattern
                id="hero-rayas"
                width="6"
                height="6"
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <rect width="3" height="6" fill="currentColor" opacity="0.55" />
              </pattern>
            </defs>
            <line x1="10" y1="130" x2="270" y2="130" stroke="currentColor" strokeWidth="1" />
            {[28, 64, 18, 92, 0, 0, 0, 44, 76, 30].map((alto, i) =>
              alto === 0 ? (
                <rect
                  key={i}
                  x={16 + i * 26}
                  y="20"
                  width="18"
                  height="110"
                  fill="url(#hero-rayas)"
                  stroke="currentColor"
                  strokeDasharray="3 3"
                />
              ) : (
                <rect
                  key={i}
                  x={16 + i * 26}
                  y={130 - alto}
                  width="18"
                  height={alto}
                  className="hero-barra"
                />
              ),
            )}
          </svg>
          <figcaption>
            Ilustración, no son datos. Las franjas rayadas son días sin dato: no significan 0 mm.
          </figcaption>
        </figure>
      </div>
      <ul className="accesos" aria-label="Accesos rápidos">
        {ACCESOS.map((a) => (
          <li key={a.ruta}>
            <Link to={a.ruta}>{a.nombre}</Link>
            <span className="nota"> — {a.texto}</span>
          </li>
        ))}
      </ul>
      <p className="nota">
        ¿Dudas sobre un color, un símbolo o una advertencia? Mirá la <Link to="/ayuda">Ayuda</Link>.
        Los datos llegan hasta el 31/10/2026.
      </p>
    </section>
  )
}
