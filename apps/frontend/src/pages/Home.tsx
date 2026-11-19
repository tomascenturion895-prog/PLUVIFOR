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
