import { useCallback, useState, type ChangeEvent, type FormEvent } from 'react'
import { ApiError, auditImport, commitImport, getImportLogs } from '../api/client'
import type { ImportKind, ImportLog, ImportReport } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { MAX_ARCHIVO_BYTES } from '../constants'
import { esConfirmable } from './importar-datos'

const TIPOS: { valor: ImportKind; nombre: string }[] = [
  { valor: 'rainfall', nombre: 'Lluvia diaria' },
  { valor: 'stations', nombre: 'Catálogo de estaciones' },
]

function mensajeDe(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
}

function leerArchivo(archivo: File): Promise<string> {
  return new Promise((resolver, rechazar) => {
    const lector = new FileReader()
    lector.onload = () => resolver(String(lector.result ?? ''))
    lector.onerror = () => rechazar(new Error('No se pudo leer el archivo.'))
    lector.readAsText(archivo)
  })
}

function validarArchivo(archivo: File): string | null {
  if (!archivo.name.toLowerCase().endsWith('.csv')) return 'El archivo debe ser un .csv.'
  if (archivo.size === 0) return 'El archivo está vacío.'
  if (archivo.size > MAX_ARCHIVO_BYTES) {
    return `El archivo supera el máximo de ${MAX_ARCHIVO_BYTES / (1024 * 1024)} MB.`
  }
  return null
}

export function Informe({ informe }: { informe: ImportReport }) {
  const guardado = informe.saved
  return (
    <section aria-labelledby="informe-titulo" className="informe">
      <h3 id="informe-titulo">{guardado ? 'Carga confirmada' : 'Informe de auditoría'}</h3>
      <p className="nota">
        {guardado
          ? 'Los datos aceptados se guardaron.'
          : 'Todavía no se guardó nada: revisá el informe y confirmá.'}
      </p>
      <dl className="resumen">
        <div>
          <dt>Filas leídas</dt>
          <dd>{informe.rows_read}</dd>
        </div>
        <div>
          <dt>Aceptadas</dt>
          <dd>{informe.rows_accepted}</dd>
        </div>
        <div>
          <dt>Rechazadas</dt>
          <dd>{informe.rows_rejected}</dd>
        </div>
        {guardado && (
          <>
            <div>
              <dt>Nuevas</dt>
              <dd>{informe.inserted}</dd>
            </div>
            <div>
              <dt>Actualizadas</dt>
              <dd>{informe.updated}</dd>
            </div>
          </>
        )}
      </dl>
      {informe.rows_accepted === 0 && (
        <p role="alert" className="estado estado-error">
          Ninguna fila es válida: no hay nada para confirmar.
        </p>
      )}
      {informe.rejections.length > 0 && (
        <>
          <h4>Filas rechazadas</h4>
          <table className="tabla-dias">
            <thead>
              <tr>
                <th scope="col">Línea</th>
                <th scope="col">Motivo</th>
              </tr>
            </thead>
            <tbody>
              {informe.rejections.map((r, i) => (
                <tr key={`${r.line}-${r.reason}-${i}`}>
                  <td>{r.line}</td>
                  <td>{r.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {informe.rejections_truncated && (
            <p className="nota">
              Se muestran solo las primeras filas rechazadas; el total está en «Rechazadas».
            </p>
          )}
        </>
      )}
    </section>
  )
}

export function Historial({ logs }: { logs: ImportLog[] }) {
  if (logs.length === 0) return <Vacio>Todavía no hay cargas registradas.</Vacio>
  return (
    <table className="tabla-dias">
      <thead>
        <tr>
          <th scope="col">Fecha</th>
          <th scope="col">Archivo</th>
          <th scope="col">Fuente</th>
          <th scope="col">Leídas</th>
          <th scope="col">Aceptadas</th>
          <th scope="col">Rechazadas</th>
        </tr>
      </thead>
      <tbody>
        {logs.map((log) => (
          <tr key={log.id}>
            <td>{new Date(log.started_at).toLocaleString('es-AR')}</td>
            <td title={`SHA-256 ${log.sha256}`}>{log.filename}</td>
            <td>{log.source}</td>
            <td>{log.rows_read}</td>
            <td>{log.rows_accepted}</td>
            <td>{log.rows_rejected}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

type Historia =
  | { tipo: 'sin_clave' }
  | { tipo: 'cargando' }
  | { tipo: 'error'; mensaje: string }
  | { tipo: 'listo'; logs: ImportLog[] }

export default function Importar() {
  // La clave solo vive en esta variable: no se guarda en el navegador ni viaja en la URL.
  const [clave, setClave] = useState('')
  const [tipo, setTipo] = useState<ImportKind>('rainfall')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [contenido, setContenido] = useState<string | null>(null)
  const [errorArchivo, setErrorArchivo] = useState<string | null>(null)
  const [informe, setInforme] = useState<ImportReport | null>(null)
  const [trabajando, setTrabajando] = useState(false)
  const [errorApi, setErrorApi] = useState<string | null>(null)
  const [historia, setHistoria] = useState<Historia>({ tipo: 'sin_clave' })

  const tienePermiso = clave.trim().length > 0
  // Sin clave el historial no se muestra aunque ya se hubiera cargado antes.
  const vista: Historia = tienePermiso ? historia : { tipo: 'sin_clave' }

  const cargarHistorial = useCallback(async (apiKey: string) => {
    setHistoria({ tipo: 'cargando' })
    try {
      setHistoria({ tipo: 'listo', logs: await getImportLogs(apiKey) })
    } catch (error) {
      setHistoria({ tipo: 'error', mensaje: mensajeDe(error) })
    }
  }, [])

  function reiniciarInforme() {
    setInforme(null)
    setErrorApi(null)
  }

  async function alElegirArchivo(evento: ChangeEvent<HTMLInputElement>) {
    reiniciarInforme()
    const elegido = evento.target.files?.[0] ?? null
    setArchivo(null)
    setContenido(null)
    setErrorArchivo(null)
    if (!elegido) return
    const problema = validarArchivo(elegido)
    if (problema) {
      setErrorArchivo(problema)
      return
    }
    try {
      setContenido(await leerArchivo(elegido))
      setArchivo(elegido)
    } catch (error) {
      setErrorArchivo(mensajeDe(error))
    }
  }

  async function ejecutar(accion: typeof auditImport) {
    if (!archivo || contenido === null || !tienePermiso || trabajando) return
    setTrabajando(true)
    setErrorApi(null)
    try {
      const resultado = await accion({
        apiKey: clave.trim(),
        kind: tipo,
        filename: archivo.name,
        content: contenido,
      })
      setInforme(resultado)
      if (resultado.saved) await cargarHistorial(clave.trim())
    } catch (error) {
      setErrorApi(mensajeDe(error))
    } finally {
      setTrabajando(false)
    }
  }

  function alAuditar(evento: FormEvent) {
    evento.preventDefault()
    void ejecutar(auditImport)
  }

  const puedeAuditar = tienePermiso && archivo !== null && !trabajando
  const puedeConfirmar = puedeAuditar && esConfirmable(informe)

  return (
    <section>
      <h2>Importar y auditar</h2>
      <p>
        Cargá un archivo CSV de la fuente SIGA/INTA y revisá qué se acepta y qué se rechaza antes de
        guardar. Un día sin valor se guarda como «sin dato», nunca como 0 mm.
      </p>

      <form className="filtros" onSubmit={alAuditar}>
        <label>
          Clave de administración
          <input
            type="password"
            autoComplete="off"
            value={clave}
            onChange={(e) => setClave(e.target.value)}
          />
        </label>
        <label>
          Tipo de archivo
          <select
            value={tipo}
            onChange={(e) => {
              setTipo(e.target.value as ImportKind)
              reiniciarInforme()
            }}
          >
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Archivo (.csv, hasta 5 MB)
          <input type="file" accept=".csv,text/csv" onChange={(e) => void alElegirArchivo(e)} />
        </label>
        <div className="acciones">
          <button type="submit" disabled={!puedeAuditar}>
            Auditar
          </button>
          <button
            type="button"
            disabled={!puedeConfirmar}
            onClick={() => void ejecutar(commitImport)}
          >
            Confirmar carga
          </button>
        </div>
      </form>

      {!tienePermiso && (
        <p className="nota">Ingresá la clave de administración para auditar y confirmar cargas.</p>
      )}
      {errorArchivo && (
        <p role="alert" className="estado estado-error">
          {errorArchivo}
        </p>
      )}
      {trabajando && <Cargando texto="Procesando archivo…" />}
      {errorApi && <ErrorEstado mensaje={errorApi} />}
      {informe && <Informe informe={informe} />}

      <h3>Historial de cargas</h3>
      {vista.tipo === 'sin_clave' && (
        <>
          <p className="nota">El historial se ve con la clave de administración.</p>
          <button
            type="button"
            disabled={!tienePermiso}
            onClick={() => void cargarHistorial(clave.trim())}
          >
            Ver historial
          </button>
        </>
      )}
      {vista.tipo === 'cargando' && <Cargando />}
      {vista.tipo === 'error' && (
        <ErrorEstado
          mensaje={vista.mensaje}
          onReintentar={() => void cargarHistorial(clave.trim())}
        />
      )}
      {vista.tipo === 'listo' && <Historial logs={vista.logs} />}
    </section>
  )
}
