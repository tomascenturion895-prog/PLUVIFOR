import { useEffect, useLayoutEffect, useRef } from 'react'
import * as THREE from 'three'
import type {
  Feature,
  FeatureCollection,
  LineString,
  MultiLineString,
  MultiPolygon,
  Polygon,
} from 'geojson'
import { normalizar } from '../maqueta/maqueta-datos'
import {
  crearBase,
  prefiereMenosMovimiento,
  texturaRayada,
  type Base,
  type Etiqueta,
} from './escena-base'
import {
  COLOR_CLASE,
  COLOR_SIN_DATO,
  nombreDepartamento,
  puntoEnDepartamento,
} from './exposicion-datos'
import {
  ALTURA_SIN_DATO,
  aspectoDepartamento,
  type Modo,
  type PinEstacion,
} from './provincia-aspecto'
import type { Departamento } from './exposicion-datos'

interface Props {
  deptos: FeatureCollection
  datos: Departamento[]
  perennes: FeatureCollection | null
  intermitentes: FeatureCollection | null
  estaciones: PinEstacion[]
  modo: Modo
  seleccionado: string | null
  onSeleccionar: (clave: string | null) => void
  onSinWebGL: () => void
}

const K = 190 // unidades de escena por grado

type Anillo = number[][]

function poligonos(f: Feature): Anillo[][] {
  const g = f.geometry as Polygon | MultiPolygon | null
  if (!g) return []
  return g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : []
}

function lineasDe(capa: FeatureCollection | null): number[][][] {
  if (!capa) return []
  return capa.features.flatMap((f) => {
    const g = f.geometry as LineString | MultiLineString | null
    if (!g) return []
    return g.type === 'LineString'
      ? [g.coordinates]
      : g.type === 'MultiLineString'
        ? g.coordinates
        : []
  })
}

interface Pieza {
  clave: string
  grupo: THREE.Group
  tapa: THREE.MeshStandardMaterial
  lado: THREE.MeshStandardMaterial
  borde: THREE.LineBasicMaterial
  alto: number
  objetivo: number
  etiqueta: Etiqueta
  centro: THREE.Vector3
  caja: THREE.Box2
}

interface Estado {
  base: Base
  piezas: Map<string, Pieza>
  rayado: THREE.CanvasTexture
  rios: { geo: THREE.BufferGeometry; depto: Int16Array; base: Float32Array }[]
  pines: { id: number; grupo: THREE.Group; depto: number; cabeza: THREE.MeshStandardMaterial }[]
  claves: string[]
}

export default function ProvinciaEscena(props: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const capa = useRef<HTMLDivElement>(null)
  const estado = useRef<Estado | null>(null)
  const ultimo = useRef(props)
  useLayoutEffect(() => {
    ultimo.current = props
  })

  // Armado de la escena: solo cuando cambian las capas geográficas.
  useEffect(() => {
    const cont = contenedor.current
    const et = capa.current
    if (!cont || !et) return
    const base = crearBase(cont, et, { sombras: true, distancia: [260, 2600] })
    if (!base) {
      ultimo.current.onSinWebGL()
      return
    }
    const { escena, camara, controles } = base
    const { deptos, perennes, intermitentes, estaciones } = ultimo.current

    const todos = deptos.features.flatMap(poligonos).flat(2)
    const lons = todos.map((p) => p[0])
    const lats = todos.map((p) => p[1])
    const lon0 = (Math.min(...lons) + Math.max(...lons)) / 2
    const lat0 = (Math.min(...lats) + Math.max(...lats)) / 2
    const kx = Math.cos((lat0 * Math.PI) / 180) * K
    const px = (lon: number) => (lon - lon0) * kx
    const pz = (lat: number) => -(lat - lat0) * K

    // Luz
    escena.add(new THREE.HemisphereLight(0xeaf4ff, 0x31424a, 1.1))
    const sol = new THREE.DirectionalLight(0xfff3e0, 1.7)
    sol.position.set(-500, 900, 600)
    sol.castShadow = true
    sol.shadow.mapSize.set(2048, 2048)
    Object.assign(sol.shadow.camera, {
      left: -700,
      right: 700,
      top: 700,
      bottom: -700,
      near: 100,
      far: 2500,
    })
    sol.shadow.bias = -0.0005
    escena.add(sol)

    // Base
    const ancho = (Math.max(...lons) - Math.min(...lons)) * kx + 160
    const fondo = (Math.max(...lats) - Math.min(...lats)) * K + 160
    const lado = Math.max(ancho, fondo) * 1.5
    const piso = new THREE.Mesh(
      new THREE.PlaneGeometry(lado, lado),
      new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.35 }),
    )
    piso.rotation.x = -Math.PI / 2
    piso.receiveShadow = true
    escena.add(piso)
    const grilla = new THREE.GridHelper(lado, 36, 0x4d7a85, 0x2a4f58)
    const matGrilla = grilla.material as THREE.Material
    matGrilla.transparent = true
    matGrilla.opacity = 0.45
    grilla.position.y = -0.2
    escena.add(grilla)

    const rayado = texturaRayada('#b9bfc2', '#8b9397')
    rayado.repeat.set(0.06, 0.06)

    const piezas = new Map<string, Pieza>()
    const claves: string[] = []
    for (const f of deptos.features) {
      const nombre = nombreDepartamento(f)
      const clave = normalizar(nombre)
      claves.push(clave)
      const grupo = new THREE.Group()
      grupo.userData.clave = clave
      const tapa = new THREE.MeshStandardMaterial({
        color: COLOR_SIN_DATO,
        roughness: 0.62,
        metalness: 0.02,
      })
      const lado = new THREE.MeshStandardMaterial({ color: COLOR_SIN_DATO, roughness: 0.8 })
      const borde = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.55,
      })
      const caja = new THREE.Box2()
      for (const [exterior, ...huecos] of poligonos(f)) {
        if (!exterior || exterior.length < 4) continue
        const forma = new THREE.Shape(exterior.map((p) => new THREE.Vector2(px(p[0]), -pz(p[1]))))
        huecos.forEach((h) =>
          forma.holes.push(new THREE.Path(h.map((p) => new THREE.Vector2(px(p[0]), -pz(p[1]))))),
        )
        const geo = new THREE.ExtrudeGeometry(forma, { depth: 1, bevelEnabled: false })
        geo.rotateX(-Math.PI / 2)
        const malla = new THREE.Mesh(geo, [tapa, lado])
        malla.castShadow = true
        malla.receiveShadow = true
        malla.userData.clave = clave
        grupo.add(malla)
        const linea = new THREE.LineLoop(
          new THREE.BufferGeometry().setFromPoints(
            exterior.map((p) => new THREE.Vector3(px(p[0]), 1.002, pz(p[1]))),
          ),
          borde,
        )
        grupo.add(linea)
        exterior.forEach((p) => caja.expandByPoint(new THREE.Vector2(px(p[0]), pz(p[1]))))
      }
      grupo.scale.y = ALTURA_SIN_DATO
      escena.add(grupo)
      const c = caja.getCenter(new THREE.Vector2())
      const centro = new THREE.Vector3(c.x, ALTURA_SIN_DATO + 10, c.y)
      piezas.set(clave, {
        clave,
        grupo,
        tapa,
        lado,
        borde,
        alto: ALTURA_SIN_DATO,
        objetivo: ALTURA_SIN_DATO,
        etiqueta: base.agregarEtiqueta(nombre, centro, 'v3d-etiqueta-depto'),
        centro,
        caja,
      })
    }

    // Cursos de agua apoyados sobre el bloque de su departamento.
    const deptoDe = (lon: number, lat: number) => {
      for (let i = 0; i < deptos.features.length; i++) {
        if (puntoEnDepartamento(lon, lat, deptos.features[i])) return i
      }
      return -1
    }
    const rios: Estado['rios'] = []
    const capasRio: [FeatureCollection | null, number, number][] = [
      [intermitentes, 0x7fb8dc, 0.55],
      [perennes, 0x0b5fa5, 1],
    ]
    for (const [capaRio, color, opacidad] of capasRio) {
      const ls = lineasDe(capaRio)
      if (!ls.length) continue
      const pos: number[] = []
      const dep: number[] = []
      for (const l of ls) {
        let anterior = deptoDe(l[0][0], l[0][1])
        for (let i = 1; i < l.length; i++) {
          const actual = deptoDe(l[i][0], l[i][1])
          // Un tramo que cruza el borde bajaría por la pared: se omite.
          if (actual === anterior) {
            for (const p of [l[i - 1], l[i]]) pos.push(px(p[0]), 0, pz(p[1]))
            dep.push(actual, actual)
          }
          anterior = actual
        }
      }
      const geo = new THREE.BufferGeometry()
      const arr = new Float32Array(pos)
      geo.setAttribute('position', new THREE.BufferAttribute(arr, 3))
      const lineas = new THREE.LineSegments(
        geo,
        new THREE.LineBasicMaterial({ color, transparent: opacidad < 1, opacity: opacidad }),
      )
      lineas.renderOrder = 2
      escena.add(lineas)
      rios.push({ geo, depto: Int16Array.from(dep), base: arr.slice() })
    }

    // Estaciones (solo las que tienen coordenadas verificadas).
    const pines: Estado['pines'] = []
    const tallo = new THREE.CylinderGeometry(0.9, 0.9, 22, 8)
    tallo.translate(0, 11, 0)
    const bola = new THREE.SphereGeometry(5, 20, 14)
    for (const e of estaciones) {
      const grupo = new THREE.Group()
      const cabeza = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 })
      grupo.add(new THREE.Mesh(tallo, new THREE.MeshStandardMaterial({ color: 0x0f2a31 })))
      const b = new THREE.Mesh(bola, cabeza)
      b.position.y = 24
      b.castShadow = true
      grupo.add(b)
      grupo.position.set(px(e.lon), 0, pz(e.lat))
      escena.add(grupo)
      pines.push({ id: e.id, grupo, depto: deptoDe(e.lon, e.lat), cabeza })
      base.agregarEtiqueta(e.nombre, grupo.position, 'v3d-etiqueta-estacion').pos = grupo.position
        .clone()
        .setY(40)
    }

    camara.position.set(-260, 820, 980)
    controles.target.set(0, 10, 40)

    const st: Estado = { base, piezas, rayado, rios, pines, claves }
    estado.current = st

    // Selección con clic o toque (si no se arrastró).
    const rc = new THREE.Raycaster()
    const ndc = new THREE.Vector2()
    let inicio: [number, number] | null = null
    let sobre: string | null = null
    const tocar = (ev: PointerEvent): string | null => {
      const r = base.renderer.domElement.getBoundingClientRect()
      ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1)
      rc.setFromCamera(ndc, camara)
      const golpe = rc
        .intersectObjects(
          [...piezas.values()].map((p) => p.grupo),
          true,
        )
        .find((i) => (i.object as THREE.Mesh).isMesh)
      return (golpe?.object.userData.clave as string | undefined) ?? null
    }
    const lienzo = base.renderer.domElement
    const abajo = (ev: PointerEvent) => {
      inicio = [ev.clientX, ev.clientY]
    }
    const arriba = (ev: PointerEvent) => {
      if (!inicio) return
      const movio = Math.hypot(ev.clientX - inicio[0], ev.clientY - inicio[1]) > 6
      inicio = null
      if (!movio) ultimo.current.onSeleccionar(tocar(ev))
    }
    const mover = (ev: PointerEvent) => {
      if (ev.buttons) return
      const c = tocar(ev)
      if (c !== sobre) {
        sobre = c
        lienzo.style.cursor = c ? 'pointer' : ''
        pintar()
      }
    }
    lienzo.addEventListener('pointerdown', abajo)
    lienzo.addEventListener('pointerup', arriba)
    lienzo.addEventListener('pointermove', mover)

    const suave = prefiereMenosMovimiento()
    const pintar = () => {
      const { datos, modo, seleccionado } = ultimo.current
      const maxDens = Math.max(0, ...datos.map((d) => d.hidrica?.densidad ?? 0))
      for (const d of datos) {
        const p = piezas.get(d.clave)
        if (!p) continue
        const { alto, color } = aspectoDepartamento(d, modo, maxDens)
        p.objetivo = alto
        if (color) {
          p.tapa.map = null
          p.tapa.color.set(color)
          p.lado.color.set(color).multiplyScalar(0.62)
          p.lado.emissive.set(color).multiplyScalar(0.18)
        } else {
          p.tapa.map = rayado
          p.tapa.color.set(0xffffff)
          p.lado.color.set(COLOR_SIN_DATO).multiplyScalar(0.7)
          p.lado.emissive.set(COLOR_SIN_DATO).multiplyScalar(0.12)
        }
        p.tapa.needsUpdate = true
        const elegido = seleccionado === d.clave
        const resaltado = elegido || sobre === d.clave
        p.tapa.emissive.set(resaltado ? 0xffffff : 0x000000)
        p.tapa.emissiveIntensity = elegido ? 0.16 : 0.08
        p.borde.opacity = elegido ? 1 : 0.5
        p.borde.color.set(elegido ? 0x0f2a31 : 0xffffff)
        p.etiqueta.el.classList.toggle('es-elegida', elegido)
      }
      const indice = new Map(ultimo.current.estaciones.map((e) => [e.id, e]))
      st.pines.forEach((pin) => {
        const e = indice.get(pin.id)
        if (!e) return
        pin.cabeza.color.set(e.descartada || !e.clase ? '#d6d6d6' : COLOR_CLASE[e.clase])
      })
    }
    st.base.alCuadro((dt) => {
      let cambio = false
      for (const p of piezas.values()) {
        if (Math.abs(p.objetivo - p.alto) < 0.05) continue
        p.alto = suave ? p.objetivo : p.alto + (p.objetivo - p.alto) * (1 - Math.exp(-dt * 9))
        p.grupo.scale.y = p.alto
        p.etiqueta.pos.y = p.alto + 10
        cambio = true
      }
      if (!cambio && st.rios.every((r) => r.geo.userData.listo)) return
      const altos = claves.map((c) => piezas.get(c)!.alto)
      for (const r of st.rios) {
        const pos = r.geo.attributes.position as THREE.BufferAttribute
        for (let i = 0; i < r.depto.length; i++) {
          pos.setY(i, r.depto[i] >= 0 ? altos[r.depto[i]] + 0.6 : 0.6)
        }
        pos.needsUpdate = true
        r.geo.userData.listo = true
      }
      for (const pin of st.pines) pin.grupo.position.y = pin.depto >= 0 ? altos[pin.depto] : 0
    })
    ;(st as Estado & { pintar?: () => void }).pintar = pintar
    pintar()

    return () => {
      lienzo.removeEventListener('pointerdown', abajo)
      lienzo.removeEventListener('pointerup', arriba)
      lienzo.removeEventListener('pointermove', mover)
      rayado.dispose()
      base.destruir()
      estado.current = null
    }
  }, [props.deptos, props.perennes, props.intermitentes, props.estaciones])

  // Datos, modo o selección nuevos: se repinta sin rearmar.
  useEffect(() => {
    ;(estado.current as (Estado & { pintar?: () => void }) | null)?.pintar?.()
  }, [props.datos, props.modo, props.seleccionado])

  return (
    <div className="v3d-lienzo-caja" ref={contenedor}>
      <div className="v3d-etiquetas" ref={capa} />
    </div>
  )
}
