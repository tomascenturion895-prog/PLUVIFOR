import { Link } from 'react-router-dom'
import { useIdioma } from '../i18n/usar-idioma'
import type { ClaveTraduccion } from '../i18n/traducciones/es'
import Icono, { type NombreIcono } from '../material/Icono'

const ACCESOS: readonly {
  ruta: string
  icono: NombreIcono
  nombre: ClaveTraduccion
  texto: ClaveTraduccion
}[] = [
  { ruta: '/vista-3d', icono: 'vista3d', nombre: 'nav.vista3d', texto: 'home.acceso.vista3d' },
  { ruta: '/maqueta', icono: 'maqueta', nombre: 'nav.maqueta', texto: 'home.acceso.maqueta' },
  { ruta: '/mapa', icono: 'mapa', nombre: 'nav.mapa', texto: 'home.acceso.mapa' },
  {
    ruta: '/comparador',
    icono: 'comparador',
    nombre: 'nav.comparador',
    texto: 'home.acceso.comparador',
  },
  { ruta: '/parte', icono: 'parte', nombre: 'nav.parte', texto: 'home.acceso.parte' },
  { ruta: '/reporte', icono: 'reporte', nombre: 'nav.reporte', texto: 'home.acceso.reporte' },
]

export default function Home() {
  const { t } = useIdioma()
  return (
    <section>
      <div className="hero">
        <div className="hero-texto">
          <h2>{t('home.titulo')}</h2>
          <p>
            {t('home.p1.inicio')}
            <strong>{t('home.p1.destacado')}</strong>
            {t('home.p1.fin')}
          </p>
          <p>{t('home.p2')}</p>
        </div>
        <figure className="hero-figura">
          <svg viewBox="0 0 280 150" role="img" aria-label={t('home.figura.aria')}>
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
          <figcaption>{t('home.figura.pie')}</figcaption>
        </figure>
      </div>
      <ul className="accesos" aria-label={t('home.accesos.aria')}>
        {ACCESOS.map((a) => (
          <li key={a.ruta}>
            <Icono nombre={a.icono} className="acceso-icono" />
            <Link to={a.ruta}>{t(a.nombre)}</Link>
            <span className="nota"> — {t(a.texto)}</span>
          </li>
        ))}
      </ul>
      <p className="nota">
        {t('home.pie.inicio')}
        <Link to="/ayuda">{t('nav.ayuda')}</Link>
        {t('home.pie.fin')}
      </p>
    </section>
  )
}
