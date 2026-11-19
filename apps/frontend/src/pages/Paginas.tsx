import { Link } from 'react-router-dom'
import { SECCIONES } from '../constants'

function Pendiente({ titulo, children }: { titulo: string; children: string }) {
  return (
    <section>
      <h2>{titulo}</h2>
      <p>{children}</p>
      <p className="nota">Esta pantalla está en construcción.</p>
    </section>
  )
}

export function Inicio() {
  return (
    <section>
      <h2>¿Cuánto llovió, dónde y en qué período?</h2>
      <p>
        PLUVIFOR muestra la lluvia de Formosa y siempre dice qué tan confiable es cada dato. Un día
        sin dato se muestra como «sin dato», nunca como 0 mm.
      </p>
      <ul className="accesos">
        {SECCIONES.filter((s) => s.ruta !== '/').map((seccion) => (
          <li key={seccion.ruta}>
            <Link to={seccion.ruta}>{seccion.nombre}</Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

export const Mapa = () => (
  <Pendiente titulo="Mapa">Lluvia acumulada por departamento y estación.</Pendiente>
)
export const Comparador = () => (
  <Pendiente titulo="Comparador">Compará estaciones y períodos con sus advertencias.</Pendiente>
)
export const Parte = () => (
  <Pendiente titulo="Parte pluvial">Resumen listo para copiar o imprimir.</Pendiente>
)
export const Salud = () => (
  <Pendiente titulo="Salud de la red">
    Qué estaciones reportan y cuáles están en silencio.
  </Pendiente>
)
export const Ayuda = () => (
  <Pendiente titulo="Ayuda">Qué significa cada estado y cada advertencia.</Pendiente>
)

export function NoEncontrada() {
  return (
    <section>
      <h2>Página no encontrada</h2>
      <p>
        No existe esta dirección. <Link to="/">Volver al inicio</Link>.
      </p>
    </section>
  )
}
