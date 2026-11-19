"""Revisa si las estaciones vecinas se pueden usar para estimar días sin dato (SCRUM-93).

Uso (desde apps/backend, con la base de demo creada):
    python ../../docs/datos/validar_estimacion.py [ruta_a_la_base.db]

Para cada par de estaciones a MAX_KM o menos con datos medidos, informa si cuentan el «día» igual
(mismo tipo y hora de corte) y cómo se parecen sus lluvias el mismo día y con un día de desfase.
Solo lee la base y no estima nada.
"""

import sqlite3
import sys
from datetime import date, timedelta
from math import sqrt

sys.path.insert(0, ".")
from app.domain.estimation import MAX_KM, distancia_km, mismo_horario  # noqa: E402

ruta = sys.argv[1] if len(sys.argv) > 1 else "pluvifor.db"
con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
estaciones = con.execute(
    "select s.id, s.name, s.lat, s.lon, s.kind, so.day_cutoff_local from stations s "
    "join sources so on so.id = s.source_id where s.coords_status = 'verificada'"
).fetchall()
medido: dict[tuple[int, str], float] = {
    (sid, fecha): mm
    for sid, fecha, mm in con.execute(
        "select station_id, obs_date, mm from rainfall_records "
        "where category = 'observado' and state = 'dato' and mm is not null"
    )
}


def correlacion(a: int, b: int, desfase: int) -> tuple[int, float]:
    """Lluvia de `a` el día D contra la de `b` el día D + desfase (solo días con ambas)."""
    xs, ys = [], []
    for (sid, fecha), mm in medido.items():
        if sid != a:
            continue
        otro = (b, (date.fromisoformat(fecha) + timedelta(days=desfase)).isoformat())
        if otro in medido:
            xs.append(mm)
            ys.append(medido[otro])
    n = len(xs)
    if n < 30:
        return n, float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    vx, vy = sum((x - mx) ** 2 for x in xs), sum((y - my) ** 2 for y in ys)
    if not vx or not vy:
        return n, float("nan")
    return n, sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sqrt(vx * vy)


hay = False
for i, (a, na, la, loa, ka, ca) in enumerate(estaciones):
    for b, nb, lb, lob, kb, cb in estaciones[i + 1 :]:
        km = distancia_km(la, loa, lb, lob)
        if km > MAX_KM:
            continue
        hay = True
        compatible = mismo_horario(ka, ca, kb, cb)
        print(f"{na}  <->  {nb}  ({km:.1f} km)")
        print(f"  tipos: «{ka}» y «{kb}» -> {'se pueden usar' if compatible else 'NO se usan'}")
        for desfase in (-1, 0, 1):
            n, r = correlacion(a, b, desfase)
            print(f"  correlación con desfase {desfase:+d} día: {r:.2f} ({n} días en común)")
if not hay:
    print(f"No hay pares de estaciones con coordenadas verificadas a {MAX_KM:g} km o menos.")
