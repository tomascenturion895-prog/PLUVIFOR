import { Link } from 'react-router-dom'

export { Mapa } from './Map'

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
