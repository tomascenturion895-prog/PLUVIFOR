import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import PanelAccesibilidad from './a11y/PanelAccesibilidad'
import SelectorIdioma from './idioma/SelectorIdioma'
import SelectorTema from './tema/SelectorTema'
import { useTema } from './tema/tema-colores'
import { SECCIONES } from '../constants'
import { useIdioma } from '../i18n/usar-idioma'
import type { ClaveTraduccion } from '../i18n/traducciones/es'
import Icono from '../material/Icono'

const CLAVE_SECCION: Record<string, ClaveTraduccion> = {
  '/': 'nav.inicio',
  '/vista-3d': 'nav.vista3d',
  '/maqueta': 'nav.maqueta',
  '/mapa': 'nav.mapa',
  '/estacion': 'nav.estacion',
  '/comparador': 'nav.comparador',
  '/parte': 'nav.parte',
  '/reporte': 'nav.reporte',
  '/importar': 'nav.importar',
  '/salud': 'nav.salud',
  '/sensores': 'nav.sensores',
  '/avisos': 'nav.avisos',
  '/cuenta': 'nav.cuenta',
  '/ayuda': 'nav.ayuda',
}

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
  // Al cambiar de tema se vuelve a dibujar el contenido: mapas, gráficos y 3D toman sus colores.
  const tema = useTema()
  const { t } = useIdioma()

  const seccionActual =
    pathname === '/'
      ? SECCIONES[0]
      : SECCIONES.find(
          (s) => s.ruta !== '/' && (pathname === s.ruta || pathname.startsWith(`${s.ruta}/`)),
        )
  const actual = seccionActual ? t(CLAVE_SECCION[seccionActual.ruta]) : t('nav.noEncontrada')

  useEffect(() => {
    document.title = `${actual} · PLUVIFOR`
  }, [actual])

  return (
    <>
      <header className="encabezado">
        <div className="encabezado-fila">
          <div className="encabezado-marca">
            <MarcaPluvifor />
            <div>
              <h1>PLUVIFOR</h1>
              <p>{t('app.subtitulo')}</p>
            </div>
          </div>
          <div className="encabezado-acciones">
            <SelectorIdioma />
            <SelectorTema />
            <PanelAccesibilidad />
          </div>
        </div>
        <nav aria-label={t('nav.etiqueta')}>
          <button
            type="button"
            className="menu-boton"
            aria-expanded={menuAbierto}
            aria-controls="menu-secciones"
            onClick={() => setMenuAbierto((a) => !a)}
          >
            <Icono nombre={menuAbierto ? 'cerrar' : 'menu'} />
            <span>
              {t('nav.menu')}
              <span className="menu-actual">: {actual}</span>
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
                  <span>{t(CLAVE_SECCION[seccion.ruta])}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main className="contenido" key={tema}>
        <Outlet />
      </main>
      <footer className="pie">
        <small>{t('app.leyendaPrototipo')}</small>
      </footer>
    </>
  )
}
