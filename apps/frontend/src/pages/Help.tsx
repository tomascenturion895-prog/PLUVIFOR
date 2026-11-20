import { InsigniaCategoria, InsigniaEstado } from '../components/Insignias'
import { ADVERTENCIAS, type CodigoAdvertencia } from '../components/insignias-datos'
import { useIdioma } from '../i18n/usar-idioma'
import type { ClaveTraduccion } from '../i18n/traducciones/es'

const CLAVE_ADV: Record<CodigoAdvertencia, { texto: ClaveTraduccion; desc: ClaveTraduccion }> = {
  horario_corte_distinto: {
    texto: 'adv.horario_corte_distinto',
    desc: 'adv.horario_corte_distinto.desc',
  },
  observado_vs_estimado: {
    texto: 'adv.observado_vs_estimado',
    desc: 'adv.observado_vs_estimado.desc',
  },
  cobertura_despareja: {
    texto: 'adv.cobertura_despareja',
    desc: 'adv.cobertura_despareja.desc',
  },
  dato_sin_validar: {
    texto: 'adv.dato_sin_validar',
    desc: 'adv.dato_sin_validar.desc',
  },
  ceros_prolongados: {
    texto: 'adv.ceros_prolongados',
    desc: 'adv.ceros_prolongados.desc',
  },
  inconsistente_con_vecinas: {
    texto: 'adv.inconsistente_con_vecinas',
    desc: 'adv.inconsistente_con_vecinas.desc',
  },
}

export default function Help() {
  const { t } = useIdioma()
  const codigos = Object.keys(ADVERTENCIAS) as CodigoAdvertencia[]
  return (
    <section>
      <h2>{t('ayuda.titulo')}</h2>
      <p>{t('ayuda.intro')}</p>

      <h3>{t('ayuda.estados.titulo')}</h3>
      <ul className="ayuda-lista">
        <li>
          <InsigniaEstado estado="dato" /> {t('ayuda.estados.dato')}
        </li>
        <li>
          <InsigniaEstado estado="sin_fila" /> {t('ayuda.estados.sin_fila')}
        </li>
        <li>
          <InsigniaEstado estado="fila_sin_valor" /> {t('ayuda.estados.fila_sin_valor')}
        </li>
      </ul>
      <p className="nota">{t('ayuda.estados.nota')}</p>

      <h3>{t('ayuda.categorias.titulo')}</h3>
      <ul className="ayuda-lista">
        <li>
          <InsigniaCategoria categoria="observado" /> {t('ayuda.categorias.observado')}
        </li>
        <li>
          <InsigniaCategoria categoria="estimado" /> {t('ayuda.categorias.estimado')}
        </li>
        <li>
          <InsigniaCategoria categoria="referencia" /> {t('ayuda.categorias.referencia')}
        </li>
      </ul>

      <h3>{t('ayuda.advertencias.titulo')}</h3>
      <p>{t('ayuda.advertencias.intro')}</p>
      <dl className="ayuda-advertencias">
        {codigos.map((codigo) => (
          <div key={codigo}>
            <dt>{t(CLAVE_ADV[codigo].texto)}</dt>
            <dd>{t(CLAVE_ADV[codigo].desc)}</dd>
          </div>
        ))}
      </dl>

      <h3>{t('ayuda.otras.titulo')}</h3>
      <ul>
        <li>
          {t('ayuda.otras.silencio.inicio')}
          <strong>{t('ayuda.otras.silencio.destacado')}</strong>
          {t('ayuda.otras.silencio.fin')}
        </li>
        <li>{t('ayuda.otras.corte')}</li>
        <li>{t('ayuda.otras.acumulados')}</li>
      </ul>
    </section>
  )
}
