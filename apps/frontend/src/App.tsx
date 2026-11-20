import { Component, Suspense, lazy, type ErrorInfo, type ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Cargando } from './components/Estados'
import Layout from './components/Layout'
import Estacion from './pages/Estacion'
import Help from './pages/Help'
import Home from './pages/Home'
import Comparador from './pages/Compare'
import FieldReport from './pages/FieldReport'
import Importar from './pages/Importar'
import NetworkHealth from './pages/NetworkHealth'
import Maqueta from './pages/Maqueta'
import Sensores from './pages/Sensores'
import Avisos from './pages/Avisos'
import Cuenta from './pages/Cuenta'
import Parte from './pages/Parte'
import { Mapa, NoEncontrada } from './pages/Paginas'

// three.js pesa: la vista 3D se descarga solo cuando se abre.
const Vista3D = lazy(() => import('./pages/Vista3D'))

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null }
  static getDerivedStateFromError(error: Error) {
    return { error }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Error renderizando pantalla:', error, info)
  }
  render() {
    if (this.state.error) {
      return (
        <section className="contenido" style={{ padding: '2rem 1rem', textAlign: 'center' }}>
          <h2>Ocurrió un error inesperado al cargar la vista</h2>
          <p className="nota" style={{ margin: '1rem 0' }}>
            {this.state.error.message}
          </p>
          <button
            type="button"
            className="acciones"
            onClick={() => {
              this.setState({ error: null })
              window.location.href = '/'
            }}
          >
            Volver al inicio
          </button>
        </section>
      )
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route
            path="vista-3d"
            element={
              <Suspense fallback={<Cargando texto="Cargando la vista 3D…" />}>
                <Vista3D />
              </Suspense>
            }
          />
          <Route path="maqueta" element={<Maqueta />} />
          <Route path="mapa" element={<Mapa />} />
          <Route path="estacion" element={<Estacion />} />
          <Route path="estacion/:id" element={<Estacion />} />
          <Route path="comparador" element={<Comparador />} />
          <Route path="parte" element={<Parte />} />
          <Route path="reporte" element={<FieldReport />} />
          <Route path="importar" element={<Importar />} />
          <Route path="salud" element={<NetworkHealth />} />
          <Route path="sensores" element={<Sensores />} />
          <Route path="avisos" element={<Avisos />} />
          <Route path="cuenta" element={<Cuenta />} />
          <Route path="ayuda" element={<Help />} />
          <Route path="*" element={<NoEncontrada />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  )
}
