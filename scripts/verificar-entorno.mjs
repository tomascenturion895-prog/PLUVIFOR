#!/usr/bin/env node
// Verifica que la computadora tenga lo necesario para trabajar en PLUVIFOR.
// Uso (desde la raíz del repositorio):   node scripts/verificar-entorno.mjs
// Funciona igual en Windows, Linux y macOS. No instala ni modifica nada.

import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), '..')
let faltan = 0

function ejecutar(comando) {
  // Solo se ejecutan comandos fijos definidos en este archivo.
  const r = spawnSync(comando, { shell: true, encoding: 'utf8' })
  if (r.status !== 0) return null
  return `${r.stdout}${r.stderr}`.trim()
}

function version(texto) {
  const m = texto && texto.match(/(\d+)\.(\d+)(?:\.(\d+))?/)
  return m ? { mayor: Number(m[1]), menor: Number(m[2]), texto: m[0] } : null
}

function mostrar(ok, etiqueta, detalle, obligatorio = true) {
  const marca = ok ? 'OK    ' : obligatorio ? 'FALTA ' : 'AVISO '
  console.log(`${marca} ${etiqueta}${detalle ? ' — ' + detalle : ''}`)
  if (!ok && obligatorio) faltan += 1
}

console.log('PLUVIFOR · verificación del entorno\n')

// Git
const git = version(ejecutar('git --version'))
mostrar(Boolean(git), 'Git', git ? git.texto : 'no se encontró (ver docs/ENTORNO.md)')

// Identidad de Git: los commits tienen que salir a nombre de cada persona.
const nombre = ejecutar('git config --global user.name')
const correo = ejecutar('git config --global user.email')
mostrar(Boolean(nombre && correo), 'Git: nombre y correo configurados', nombre && correo ? `${nombre} <${correo}>` : 'configurar user.name y user.email')

// Python 3.12 o superior (se prueban los nombres habituales según el sistema)
let python = null
for (const cmd of ['python --version', 'python3 --version', 'py -3.12 --version', 'py -3 --version']) {
  const v = version(ejecutar(cmd))
  if (v && (v.mayor > 3 || (v.mayor === 3 && v.menor >= 12))) {
    python = { v, cmd: cmd.replace(' --version', '') }
    break
  }
}
mostrar(Boolean(python), 'Python 3.12 o superior', python ? `${python.v.texto} (comando: ${python.cmd})` : 'no se encontró una versión 3.12+')

// Node.js 22 o superior (el propio proceso)
const node = version(process.version)
mostrar(node.mayor >= 22, 'Node.js 22 o superior', node.texto)

// Go 1.24 o superior (solo para la API en Go: la demo corre sin Go desde el backend en Python)
const go = version(ejecutar('go version'))
mostrar(Boolean(go) && (go.mayor > 1 || go.menor >= 24), 'Go 1.24 o superior (API en Go)', go ? go.texto : 'sin instalar (https://go.dev/dl/); hace falta solo para apps/api-go', false)

// npm
const npm = version(ejecutar('npm --version'))
mostrar(Boolean(npm), 'npm', npm ? npm.texto : 'no se encontró')

// pre-commit (opcional pero recomendado: frena secretos antes de cada commit)
const pc = version(ejecutar('pre-commit --version'))
mostrar(Boolean(pc), 'pre-commit', pc ? pc.texto : 'sin instalar (pip install pre-commit; ver docs/seguridad-secretos.md)', false)

// Estructura del repositorio
for (const ruta of ['AGENTS.md', 'apps', 'docs', 'apps/api-go']) {
  mostrar(existsSync(join(raiz, ruta)), `Repositorio: ${ruta}`, existsSync(join(raiz, ruta)) ? '' : 'no está; ¿corriste el comando en la raíz del repo y hiciste git pull?', ruta === 'AGENTS.md' || ruta === 'apps/api-go' ? false : true)
}

// Archivo de variables de entorno
mostrar(existsSync(join(raiz, '.env')), 'Archivo .env', existsSync(join(raiz, '.env')) ? '' : 'copiar .env.example a .env', false)

console.log('')
if (faltan === 0) {
  console.log('Todo listo para trabajar.')
} else {
  console.log(`Faltan ${faltan} cosa(s) obligatoria(s). Seguí los pasos de docs/ENTORNO.md y volvé a correr este comando.`)
  process.exitCode = 1
}
