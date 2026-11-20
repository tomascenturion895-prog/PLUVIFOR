import { useState, type FormEvent } from 'react'
import { useSesion } from '../auth/usar-sesion'
import { ApiError, postFieldReport } from '../api/client'
import type { FieldReport as Reporte } from '../api/types'
import { ErrorEstado } from '../components/Estados'
import { FECHA_CORTE } from '../constants'
import { useIdioma } from '../i18n/usar-idioma'
import { armarPedido, fechaLegible, type FormularioReporte } from './field-report-datos'

const VACIO: FormularioReporte = {
  fecha: '',
  mm: '',
  lugar: '',
  quien: '',
  lat: '',
  lon: '',
  origen: null,
}

export default function FieldReport() {
  const { t } = useIdioma()
  // La clave solo vive en esta variable: no se guarda en el navegador ni viaja en la URL.
  const { esPersonal } = useSesion()
  const [clave, setClave] = useState('')
  const [f, setF] = useState<FormularioReporte>(VACIO)
  const [errores, setErrores] = useState<string[]>([])
  const [errorApi, setErrorApi] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [guardado, setGuardado] = useState<Reporte | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  const cambiar = (campo: keyof FormularioReporte, valor: string) => {
    setF((actual) => {
      const siguiente = { ...actual, [campo]: valor }
      // Si tocan la ubicación a mano, deja de ser la del dispositivo.
      if (campo === 'lat' || campo === 'lon') siguiente.origen = 'manual'
      return siguiente
    })
  }

  function usarMiUbicacion() {
    setAviso(null)
    if (!('geolocation' in navigator)) {
      setAviso('Tu navegador no permite obtener la ubicación. Escribila a mano o dejala vacía.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setF((actual) => ({
          ...actual,
          lat: pos.coords.latitude.toFixed(5),
          lon: pos.coords.longitude.toFixed(5),
          origen: 'dispositivo',
        })),
      () =>
        setAviso(
          'No se pudo obtener la ubicación (no diste permiso o no hay señal). Escribila a mano o dejala vacía: el reporte queda con ubicación pendiente.',
        ),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setGuardado(null)
    setErrorApi(null)
    const resultado = armarPedido(f)
    if (!resultado.ok) {
      setErrores(resultado.errores)
      return
    }
    if (!esPersonal && clave.trim() === '') {
      setErrores(['Ingresá la clave para cargar reportes.'])
      return
    }
    setErrores([])
    setEnviando(true)
    try {
      setGuardado(await postFieldReport(clave.trim(), resultado.pedido))
      setF(VACIO)
    } catch (e) {
      setErrorApi(e instanceof ApiError ? e.message : 'Ocurrió un error inesperado.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section>
      <h2>{t('nav.reporte')}</h2>
      <p>
        Donde no hay estación, la lluvia la anota la policía por día. Cargá acá ese reporte: queda
        como <strong>observado y sin validar</strong>, con la fuente «reporte policial», y no se
        mezcla con lo que miden las estaciones.
      </p>
      <form className="filtros" onSubmit={(e) => void enviar(e)} noValidate>
        {!esPersonal && (
          <label>
            {t('reporte.clave')}
            <input
              type="password"
              autoComplete="off"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
            />
          </label>
        )}
        <label>
          {t('reporte.fechaLluvia')}
          <input
            type="date"
            value={f.fecha}
            max={FECHA_CORTE}
            onChange={(e) => cambiar('fecha', e.target.value)}
          />
        </label>
        <label>
          {t('reporte.milimetros')}
          <input
            inputMode="decimal"
            placeholder="12,5"
            value={f.mm}
            onChange={(e) => cambiar('mm', e.target.value)}
          />
        </label>
        <label>
          {t('reporte.lugar')}
          <input
            maxLength={200}
            placeholder={t('reporte.lugarPlaceholder')}
            value={f.lugar}
            onChange={(e) => cambiar('lugar', e.target.value)}
          />
        </label>
        <label>
          {t('reporte.quien')}
          <input
            maxLength={120}
            value={f.quien}
            onChange={(e) => cambiar('quien', e.target.value)}
          />
        </label>
        <fieldset>
          <legend>{t('reporte.ubicacion')}</legend>
          <button type="button" onClick={usarMiUbicacion}>
            {t('reporte.usarUbicacion')}
          </button>
          <label>
            {t('reporte.latitud')}
            <input
              inputMode="decimal"
              placeholder="-26,18"
              value={f.lat}
              onChange={(e) => cambiar('lat', e.target.value)}
            />
          </label>
          <label>
            {t('reporte.longitud')}
            <input
              inputMode="decimal"
              placeholder="-58,17"
              value={f.lon}
              onChange={(e) => cambiar('lon', e.target.value)}
            />
          </label>
          <p className="nota">
            Si no la informás, el reporte queda con ubicación <strong>pendiente</strong>: no se
            inventa.
          </p>
          {aviso && (
            <p role="status" className="nota">
              {aviso}
            </p>
          )}
        </fieldset>
        <div className="acciones">
          <button type="submit" disabled={enviando}>
            {enviando ? 'Enviando…' : 'Enviar reporte'}
          </button>
        </div>
      </form>
      {errores.length > 0 && (
        <div role="alert" className="estado estado-error">
          <ul>
            {errores.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      {errorApi && <ErrorEstado mensaje={errorApi} />}
      {guardado && (
        <p role="status" className="estado">
          Reporte guardado: {fechaLegible(guardado.obs_date)} · {guardado.mm} mm · {guardado.place}.
          Quedó <strong>observado, sin validar</strong>, fuente reporte policial
          {guardado.location_status === 'pendiente'
            ? ', con ubicación pendiente.'
            : ` y ubicación ${guardado.location_source === 'dispositivo' ? 'del dispositivo' : 'cargada a mano'}.`}
        </p>
      )}
    </section>
  )
}
