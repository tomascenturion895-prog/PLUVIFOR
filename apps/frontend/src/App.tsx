import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Estacion from './pages/Estacion'
import Help from './pages/Help'
import Home from './pages/Home'
import Comparador from './pages/Compare'
import FieldReport from './pages/FieldReport'
import Importar from './pages/Importar'
import NetworkHealth from './pages/NetworkHealth'
import Parte from './pages/Parte'
import { Mapa, NoEncontrada } from './pages/Paginas'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="mapa" element={<Mapa />} />
        <Route path="estacion" element={<Estacion />} />
        <Route path="estacion/:id" element={<Estacion />} />
        <Route path="comparador" element={<Comparador />} />
        <Route path="parte" element={<Parte />} />
        <Route path="reporte" element={<FieldReport />} />
        <Route path="importar" element={<Importar />} />
        <Route path="salud" element={<NetworkHealth />} />
        <Route path="ayuda" element={<Help />} />
        <Route path="*" element={<NoEncontrada />} />
      </Route>
    </Routes>
  )
}
