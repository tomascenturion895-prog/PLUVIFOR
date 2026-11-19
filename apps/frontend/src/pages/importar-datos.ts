import type { ImportReport } from '../api/types'

/** Un informe es confirmable si aceptó al menos una fila. Los rechazos se muestran, no se ocultan. */
export function esConfirmable(informe: ImportReport | null): boolean {
  return informe !== null && informe.mode === 'audit' && informe.rows_accepted > 0
}
