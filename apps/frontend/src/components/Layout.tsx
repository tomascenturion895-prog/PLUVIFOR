import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import PanelAccesibilidad from './a11y/PanelAccesibilidad'
import SelectorTema from './tema/SelectorTema'
import { LEYENDA_PROTOTIPO, SECCIONES } from '../constants'
import { tituloDe } from '../titulos'
import Icono from '../material/Icono'

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
  const { pathname } = useLocation()
  const [menuAbierto, setMenuAbierto] = useState(false)
  useEffect(() => {
    document.title = tituloDe(pathname)
  }, [pathname])
  const actual = tituloDe(pathname).replace(' · PLUVIFOR', '')

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
          <div className="encabezado-acciones">
            <SelectorTema />
            <PanelAccesibilidad />
          </div>
        </div>
        <nav aria-label="Secciones">
          <button
            type="button"
            className="menu-boton"
            aria-expanded={menuAbierto}
            aria-controls="menu-secciones"
            onClick={() => setMenuAbierto((a) => !a)}
          >
            <Icono nombre={menuAbierto ? 'cerrar' : 'menu'} />
            <span>
              Menú<span className="menu-actual">: {actual}</span>
            </span>
          </button>
          <ul id="menu-secciones" className={menuAbierto ? 'abierto' : ''}>
            {SECCIONES.map((seccion) => (
              <li key={seccion.ruta}>
                <NavLink
                  to={seccion.ruta}
                  end={seccion.ruta === '/'}
                  onClick={() => setMenuAbierto(false)}
                >
                  <Icono nombre={seccion.icono} />
                  <span>{seccion.nombre}</span>
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
