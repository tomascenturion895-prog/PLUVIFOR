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
import App from './App.tsx'

// El tema se aplica antes de pintar, para que no parpadee el oscuro al recargar en claro.
aplicarTema(document.documentElement, leerTema(almacenLocal()))

const raiz = document.getElementById('root')!
instalarOndas(raiz)

createRoot(raiz).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
