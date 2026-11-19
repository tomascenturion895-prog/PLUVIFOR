import { InsigniaCategoria, InsigniaEstado } from '../components/Insignias'
import { ADVERTENCIAS, type CodigoAdvertencia } from '../components/insignias-datos'

export default function Help() {
  const codigos = Object.keys(ADVERTENCIAS) as CodigoAdvertencia[]
  return (
    <section>
      <h2>Ayuda</h2>
      <p>Qué significa cada estado de un día, cada categoría de dato y cada advertencia.</p>

      <h3>Estados de un día</h3>
      <ul className="ayuda-lista">
        <li>
          <InsigniaEstado estado="dato" /> Hay una medición para ese día. Un «0 mm» con este estado
          es lluvia cero medida.
        </li>
        <li>
          <InsigniaEstado estado="sin_fila" /> La fuente no tiene ese día. No significa que no haya
          llovido.
        </li>
        <li>
          <InsigniaEstado estado="fila_sin_valor" /> La fuente tiene el día pero sin un valor.
          Tampoco significa que no haya llovido.
        </li>
      </ul>
      <p className="nota">
        Los días sin dato se cuentan aparte y nunca entran como 0 mm en un acumulado.
      </p>

      <h3>Categorías del dato</h3>
      <ul className="ayuda-lista">
        <li>
          <InsigniaCategoria categoria="observado" /> Medido por una estación o un reporte.
        </li>
        <li>
          <InsigniaCategoria categoria="estimado" /> Calculado, no medido. Nunca se suma ni se
          promedia con lo observado.
        </li>
        <li>
          <InsigniaCategoria categoria="referencia" /> Valor de referencia, como una normal
          climática. Tampoco se mezcla con lo observado.
        </li>
      </ul>

      <h3>Las 6 advertencias de comparabilidad</h3>
      <p>
        Avisan cuando dos datos no se pueden comparar de igual a igual. Son descriptivas: no son
        alertas de riesgo.
      </p>
      <dl className="ayuda-advertencias">
        {codigos.map((codigo) => (
          <div key={codigo}>
            <dt>{ADVERTENCIAS[codigo].texto}</dt>
            <dd>{ADVERTENCIAS[codigo].descripcion}</dd>
          </div>
        ))}
      </dl>

      <h3>Otras cosas para tener en cuenta</h3>
      <ul>
        <li>
          Una estación <strong>en silencio</strong> es la que dejó de reportar: se ve apagada y
          nunca con el color de 0 mm.
        </li>
        <li>Los datos llegan hasta el 31/10/2026; no se usan días posteriores.</li>
        <li>Los acumulados de estaciones distintas no se suman: cada estación tiene el suyo.</li>
      </ul>
    </section>
  )
}
