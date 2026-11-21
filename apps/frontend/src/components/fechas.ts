/** Resta días a una fecha AAAA-MM-DD, en UTC para no depender de la zona horaria. */
export function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}
