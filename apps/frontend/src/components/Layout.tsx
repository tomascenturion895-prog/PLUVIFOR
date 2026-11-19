import { NavLink, Outlet } from 'react-router-dom'
import { LEYENDA_PROTOTIPO, SECCIONES } from '../constants'

export default function Layout() {
  return (
    <>
      <header className="encabezado">
        <div className="encabezado-marca">
          <h1>PLUVIFOR</h1>
          <p>Reporte pluvial de Formosa</p>
        </div>
        <nav aria-label="Secciones">
          <ul>
            {SECCIONES.map((seccion) => (
              <li key={seccion.ruta}>
                <NavLink to={seccion.ruta} end={seccion.ruta === '/'}>
                  {seccion.nombre}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
      <footer className="pie">
        <small>{LEYENDA_PROTOTIPO}</small>
      </footer>
    </>
  )
}
