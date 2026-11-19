import { NavLink, Outlet } from 'react-router-dom'
import PanelAccesibilidad from './a11y/PanelAccesibilidad'
import { LEYENDA_PROTOTIPO, SECCIONES } from '../constants'

/** Barras de lluvia diaria; la del medio va rayada porque un día sin dato no es 0 mm. */
function MarcaPluvifor() {
  return (
    <svg className="marca-logo" viewBox="0 0 40 32" aria-hidden="true" focusable="false">
      <defs>
        <pattern
          id="marca-rayas"
          width="4"
          height="4"
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <rect width="4" height="4" fill="none" />
          <rect width="2" height="4" fill="currentColor" />
        </pattern>
      </defs>
      <rect x="2" y="14" width="6" height="16" rx="1" fill="currentColor" />
      <rect x="11" y="6" width="6" height="24" rx="1" fill="currentColor" />
      <rect
        x="20"
        y="4"
        width="6"
        height="26"
        rx="1"
        fill="url(#marca-rayas)"
        stroke="currentColor"
        strokeWidth="1"
      />
      <rect x="29" y="18" width="6" height="12" rx="1" fill="currentColor" />
    </svg>
  )
}

export default function Layout() {
  return (
    <>
      <header className="encabezado">
        <div className="encabezado-fila">
          <div className="encabezado-marca">
            <MarcaPluvifor />
            <div>
              <h1>PLUVIFOR</h1>
              <p>Reporte pluvial de Formosa</p>
            </div>
          </div>
          <PanelAccesibilidad />
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
