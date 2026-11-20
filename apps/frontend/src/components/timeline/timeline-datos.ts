/** Línea de tiempo mes a mes (SCRUM-99). */

export interface Mes {
  desde: string
  hasta: string
  /** «2015-10», para mostrar y para las pruebas. */
  clave: string
}

const pad = (n: number) => String(n).padStart(2, '0')

function ultimoDiaDelMes(anio: number, mes: number): number {
  return new Date(Date.UTC(anio, mes, 0)).getUTCDate() // mes: 1 a 12
}

/**
 * Los meses que toca el período, de a uno. El primero y el último pueden ser parciales: nunca
 * se sale del período pedido ni se pasa de la fecha de corte.
 */
export function mesesDelPeriodo(desde: string, hasta: string, corte: string): Mes[] {
  const fin = hasta < corte ? hasta : corte
  if (!/^\d{4}-\d{2}-\d{2}$/.test(desde) || !/^\d{4}-\d{2}-\d{2}$/.test(fin) || desde > fin) {
    return []
  }
  const meses: Mes[] = []
  let anio = Number(desde.slice(0, 4))
  let mes = Number(desde.slice(5, 7))
  for (;;) {
    const clave = `${anio}-${pad(mes)}`
    const primero = `${clave}-01`
    const ultimo = `${clave}-${pad(ultimoDiaDelMes(anio, mes))}`
    meses.push({
      clave,
      desde: primero < desde ? desde : primero,
      hasta: ultimo > fin ? fin : ultimo,
    })
    if (ultimo >= fin) break
    mes += 1
    if (mes > 12) {
      mes = 1
      anio += 1
    }
  }
  return meses
}

/** Paso de la reproducción: avanza un mes y se detiene en el último. */
export function siguiente(indice: number, total: number): { indice: number; termino: boolean } {
  if (total <= 0) return { indice: 0, termino: true }
  const proximo = Math.min(indice + 1, total - 1)
  return { indice: proximo, termino: proximo >= total - 1 }
}
