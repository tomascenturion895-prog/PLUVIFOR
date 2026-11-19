import { ATAJOS, type Atajo } from './atajos'

export default function Atajos({
  activo,
  alElegir,
}: {
  activo: Atajo['id'] | null
  alElegir: (atajo: Atajo) => void
}) {
  return (
    <section className="atajos" aria-label="Atajos">
      <h3>Atajos</h3>
      <ul>
        {ATAJOS.map((a) => (
          <li key={a.id}>
            <button type="button" aria-pressed={activo === a.id} onClick={() => alElegir(a)}>
              {a.nombre}
            </button>
            <span className="nota"> {a.descripcion}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
