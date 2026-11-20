import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './maqueta3d.css'
import './vista3d.css'
import './pulido.css'
import './material/registro'
import './material.css'
import './theme.css'
import './temas.css'
import { instalarOndas } from './material/ondas'
import { aplicarTema, almacenLocal, leerTema } from './components/tema/tema-datos'
import { ProveedorIdioma } from './i18n/contexto'
import { almacenLocal as almacenIdioma, aplicarIdioma, leerIdioma } from './i18n/idioma-datos'
import App from './App.tsx'

// El tema y el idioma se aplican antes de pintar, para evitar parpadeos al recargar.
aplicarTema(document.documentElement, leerTema(almacenLocal()))
aplicarIdioma(document.documentElement, leerIdioma(almacenIdioma()))

const raiz = document.getElementById('root')!
instalarOndas(raiz)

createRoot(raiz).render(
  <StrictMode>
    <ProveedorIdioma>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ProveedorIdioma>
  </StrictMode>,
)
