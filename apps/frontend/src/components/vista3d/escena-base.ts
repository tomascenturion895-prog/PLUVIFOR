import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

/** true si el navegador puede dibujar WebGL. En las pruebas (jsdom) da false. */
export function hayWebGL(): boolean {
  try {
    const c = document.createElement('canvas')
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')))
  } catch {
    return false
  }
}

export function prefiereMenosMovimiento(): boolean {
  return (
    document.documentElement.dataset.movimiento === 'reducido' ||
    (typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  )
}

export interface Etiqueta {
  el: HTMLDivElement
  pos: THREE.Vector3
}

export interface Base {
  renderer: THREE.WebGLRenderer
  escena: THREE.Scene
  camara: THREE.PerspectiveCamera
  controles: OrbitControls
  etiquetas: Etiqueta[]
  agregarEtiqueta: (texto: string, pos: THREE.Vector3, clase?: string) => Etiqueta
  limpiarEtiquetas: () => void
  /** Registra lo que se hace en cada cuadro; recibe los segundos transcurridos. */
  alCuadro: (fn: (dt: number) => void) => void
  destruir: () => void
}

/**
 * Arma lo común de una escena: renderer transparente (el fondo lo pone el CSS), cámara con
 * órbita amortiguada, capa de etiquetas en HTML y el ciclo de dibujo. Devuelve null sin WebGL.
 */
export function crearBase(
  contenedor: HTMLElement,
  capaEtiquetas: HTMLElement,
  opciones: { sombras?: boolean; distancia: [number, number] },
): Base | null {
  let renderer: THREE.WebGLRenderer
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  } catch {
    return null
  }
  const angosto = contenedor.clientWidth < 760
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, angosto ? 1.5 : 2))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05
  renderer.shadowMap.enabled = !!opciones.sombras && !angosto
  renderer.shadowMap.type = THREE.PCFShadowMap
  renderer.domElement.className = 'v3d-lienzo'
  contenedor.prepend(renderer.domElement)

  const escena = new THREE.Scene()
  const camara = new THREE.PerspectiveCamera(36, 1, 5, 12000)
  const controles = new OrbitControls(camara, renderer.domElement)
  controles.enableDamping = true
  controles.dampingFactor = 0.08
  controles.minDistance = opciones.distancia[0]
  controles.maxDistance = opciones.distancia[1]
  controles.maxPolarAngle = 1.32
  controles.autoRotate = !prefiereMenosMovimiento()
  controles.autoRotateSpeed = 0.35
  const detenerGiro = () => {
    controles.autoRotate = false
  }
  controles.addEventListener('start', detenerGiro)

  const etiquetas: Etiqueta[] = []
  const agregarEtiqueta = (texto: string, pos: THREE.Vector3, clase = '') => {
    const el = document.createElement('div')
    el.className = `v3d-etiqueta ${clase}`.trim()
    el.textContent = texto
    el.setAttribute('aria-hidden', 'true')
    capaEtiquetas.appendChild(el)
    const e = { el, pos }
    etiquetas.push(e)
    return e
  }
  const limpiarEtiquetas = () => {
    etiquetas.splice(0).forEach((e) => e.el.remove())
  }

  const tmp = new THREE.Vector3()
  const ubicarEtiquetas = () => {
    const W = renderer.domElement.clientWidth
    const H = renderer.domElement.clientHeight
    for (const e of etiquetas) {
      tmp.copy(e.pos).project(camara)
      const visible = tmp.z < 1 && Math.abs(tmp.x) < 1.02 && Math.abs(tmp.y) < 1.02
      e.el.style.display = visible ? '' : 'none'
      if (visible) {
        e.el.style.transform = `translate(${((tmp.x + 1) / 2) * W}px, ${((1 - tmp.y) / 2) * H}px) translate(-50%, -50%)`
      }
    }
  }

  const ajustar = () => {
    const W = contenedor.clientWidth
    const H = contenedor.clientHeight
    if (!W || !H) return
    renderer.setSize(W, H, false)
    camara.aspect = W / H
    camara.updateProjectionMatrix()
  }
  const observador = new ResizeObserver(ajustar)
  observador.observe(contenedor)
  ajustar()

  const tareas: ((dt: number) => void)[] = []
  let antes = performance.now()
  let activo = true
  renderer.setAnimationLoop((ahora: number) => {
    if (!activo) return
    const dt = Math.min(0.05, Math.max(0, (ahora - antes) / 1000))
    antes = ahora
    tareas.forEach((t) => t(dt))
    controles.update()
    ubicarEtiquetas()
    renderer.render(escena, camara)
  })

  return {
    renderer,
    escena,
    camara,
    controles,
    etiquetas,
    agregarEtiqueta,
    limpiarEtiquetas,
    alCuadro: (fn) => tareas.push(fn),
    destruir: () => {
      activo = false
      renderer.setAnimationLoop(null)
      observador.disconnect()
      controles.dispose()
      limpiarEtiquetas()
      escena.traverse((o) => {
        const m = o as THREE.Mesh
        m.geometry?.dispose()
        const mats = Array.isArray(m.material) ? m.material : m.material ? [m.material] : []
        mats.forEach((mat) => {
          Object.values(mat).forEach((v) => {
            if (v instanceof THREE.Texture) v.dispose()
          })
          mat.dispose()
        })
      })
      renderer.dispose()
      renderer.domElement.remove()
    },
  }
}

/** Textura rayada para «sin dato»: nunca un color liso que se confunda con un valor. */
export function texturaRayada(fondo: string, raya: string): THREE.CanvasTexture {
  const c = document.createElement('canvas')
  c.width = c.height = 64
  const g = c.getContext('2d')!
  g.fillStyle = fondo
  g.fillRect(0, 0, 64, 64)
  g.strokeStyle = raya
  g.lineWidth = 10
  for (let i = -64; i < 128; i += 22) {
    g.beginPath()
    g.moveTo(i, 64)
    g.lineTo(i + 64, 0)
    g.stroke()
  }
  const t = new THREE.CanvasTexture(c)
  t.wrapS = t.wrapT = THREE.RepeatWrapping
  t.colorSpace = THREE.SRGBColorSpace
  return t
}
