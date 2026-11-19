import inicio from '@material-symbols/svg-400/rounded/home.svg?raw'
import vista3d from '@material-symbols/svg-400/rounded/view_in_ar.svg?raw'
import maqueta from '@material-symbols/svg-400/rounded/landscape.svg?raw'
import mapa from '@material-symbols/svg-400/rounded/map.svg?raw'
import estacion from '@material-symbols/svg-400/rounded/rainy.svg?raw'
import comparador from '@material-symbols/svg-400/rounded/compare_arrows.svg?raw'
import parte from '@material-symbols/svg-400/rounded/description.svg?raw'
import reporte from '@material-symbols/svg-400/rounded/edit_note.svg?raw'
import importar from '@material-symbols/svg-400/rounded/upload_file.svg?raw'
import salud from '@material-symbols/svg-400/rounded/monitor_heart.svg?raw'
import ayuda from '@material-symbols/svg-400/rounded/help.svg?raw'
import accesibilidad from '@material-symbols/svg-400/rounded/accessibility_new.svg?raw'
import menu from '@material-symbols/svg-400/rounded/menu.svg?raw'
import cerrar from '@material-symbols/svg-400/rounded/close.svg?raw'

/** Íconos Material Symbols (redondeados) que usa la interfaz, embebidos como SVG. */
const ICONOS = {
  inicio,
  vista3d,
  maqueta,
  mapa,
  estacion,
  comparador,
  parte,
  reporte,
  importar,
  salud,
  ayuda,
  accesibilidad,
  menu,
  cerrar,
} as const

export type NombreIcono = keyof typeof ICONOS

/** Ícono decorativo de Material: el texto que lo acompaña es el que se lee. */
export default function Icono({ nombre, className }: { nombre: NombreIcono; className?: string }) {
  return (
    <md-icon
      aria-hidden="true"
      className={className}
      dangerouslySetInnerHTML={{ __html: ICONOS[nombre] }}
    />
  )
}
