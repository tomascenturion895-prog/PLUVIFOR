"""Línea de comandos: `python -m app.cli --help`.

Importar es una acción de quien administra la base; no se expone por la API pública.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from app.config import get_settings
from app.db.session import create_db_engine, create_session_factory
from app.demo import DEFAULT_DATA_DIR, DemoResetError, reset_demo
from app.domain.enums import ImportMode
from app.ingestion.siga_live import SigaLiveClient
from app.ingestion.types import ImportReport, InvalidFileError
from app.repositories.gap_estimates import SqlGapEstimateRepository
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.quality import SqlQualityRepository
from app.repositories.references import SqlReferenceRepository
from app.services.gap_estimation import GapEstimationService
from app.services.importer import ImportService
from app.services.quality import QualityService
from app.services.references import ReferenceService
from app.services.siga_live import SigaLiveImporter

DEFAULT_NORMALS_FILE = DEFAULT_DATA_DIR / "normales_smn_formosa_aero_1991_2020.csv"


def _print_report(report: ImportReport) -> None:
    print(f"Archivo: {report.filename}  sha256: {report.sha256[:12]}…  modo: {report.mode}")
    print(
        f"Leídas: {report.rows_read} · aceptadas: {report.rows_accepted} "
        f"· rechazadas: {report.rows_rejected}"
    )
    for reason, count in sorted(report.rejections_by_reason().items()):
        print(f"  rechazo {reason}: {count}")
    if report.mode == ImportMode.COMMIT.value:
        print(f"Guardadas: {report.inserted} nuevas, {report.updated} actualizadas")
    else:
        print("Simulación (audit): no se guardó ningún dato.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pluvifor", description="Herramientas de PLUVIFOR")
    commands = parser.add_subparsers(dest="command", required=True)

    stations = commands.add_parser("import-stations", help="Importa el catálogo de estaciones")
    stations.add_argument("--source", default="siga_inta")
    stations.add_argument("file", type=Path)

    rainfall = commands.add_parser("import-rainfall", help="Importa lluvia diaria")
    rainfall.add_argument("--source", default="siga_inta")
    rainfall.add_argument(
        "--commit", action="store_true", help="Guarda los datos (por defecto solo audita)"
    )
    rainfall.add_argument("file", type=Path)

    live = commands.add_parser(
        "import-siga-live",
        help="Pide lluvia diaria al SIGA en vivo; si falla, usa el CSV versionado y lo avisa",
    )
    live.add_argument("--station", type=int, action="append", required=True)
    live.add_argument("--from", dest="date_from", type=date.fromisoformat, required=True)
    live.add_argument("--to", dest="date_to", type=date.fromisoformat, required=True)
    live.add_argument("--commit", action="store_true", help="Guarda (por defecto solo audita)")

    commands.add_parser("recompute-flags", help="Recalcula las banderas de calidad")

    estimate = commands.add_parser(
        "estimate-gaps",
        help="Estima días sin dato con vecinas y CHIRPS (valores estimados, nunca medidos)",
    )
    estimate.add_argument("--from", dest="date_from", type=date.fromisoformat, required=True)
    estimate.add_argument("--to", dest="date_to", type=date.fromisoformat, required=True)
    estimate.add_argument("--station-id", type=int, help="Una sola estación (por defecto, todas)")
    estimate.add_argument(
        "--dry-run", action="store_true", help="Calcula y cuenta, pero no guarda nada"
    )

    normals = commands.add_parser(
        "import-normals", help="Carga la normal mensual (referencia) con su fuente"
    )
    normals.add_argument("file", type=Path, nargs="?", default=DEFAULT_NORMALS_FILE)

    demo = commands.add_parser(
        "reset-demo", help="Borra la base SQLite y la recarga desde docs/datos (sin internet)"
    )
    demo.add_argument("--yes", action="store_true", help="No pedir confirmación")
    demo.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    return parser


def _ask_before_deleting(database: Path) -> bool:
    if not sys.stdin.isatty():
        print("Sin una terminal para confirmar: usá --yes para reiniciar.", file=sys.stderr)
        return False
    answer = input(f"Se va a BORRAR la base {database} y a recargarla desde cero. ¿Seguro? [s/N] ")
    return answer.strip().lower() in {"s", "si", "sí"}


def _reset_demo(args: argparse.Namespace) -> int:
    settings = get_settings()
    confirm = (lambda _: True) if args.yes else _ask_before_deleting
    try:
        result = reset_demo(
            settings.database_url, settings.data_cutoff_date, confirm, args.data_dir
        )
    except DemoResetError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if result is None:
        print("No se reinició nada.")
        return 1
    print(f"Base reiniciada: {result.database}")
    print(
        f"Estaciones: {result.stations} · días de lluvia: {result.rainfall_rows} "
        f"· rechazados: {result.rejected_rows} · tramos de ceros prolongados: {result.zero_streaks}"
    )
    return 0


def _recompute_flags(session) -> None:
    """Tras guardar lluvia se recalculan las banderas: así no quedan desactualizadas."""
    counts = QualityService(SqlQualityRepository(session)).recompute_zero_streaks()
    print(f"Banderas recalculadas · tramos de ceros prolongados: {sum(counts.values())}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "reset-demo":
        return _reset_demo(args)
    settings = get_settings()
    engine = create_db_engine(settings.database_url)
    try:
        if args.command == "import-normals":
            with create_session_factory(engine)() as session:
                done = ReferenceService(SqlReferenceRepository(session)).import_normals(
                    args.file.name, args.file.read_bytes()
                )
            print(
                f"Normal cargada: estación {done.station_code}, {done.months} meses, {done.period}"
            )
            return 0
        if args.command == "recompute-flags":
            with create_session_factory(engine)() as session:
                counts = QualityService(SqlQualityRepository(session)).recompute_zero_streaks()
            print(
                f"Estaciones revisadas: {len(counts)} · "
                f"tramos de ceros prolongados: {sum(counts.values())}"
            )
            return 0
        if args.command == "estimate-gaps":
            with create_session_factory(engine)() as session:
                service = GapEstimationService(
                    SqlGapEstimateRepository(session), settings.data_cutoff_date
                )
                try:
                    done = service.run(
                        args.date_from, args.date_to, args.station_id, dry_run=args.dry_run
                    )
                except ValueError as exc:
                    print(f"Error: {exc}", file=sys.stderr)
                    return 1
            print(
                f"Días sin dato revisados: {done.huecos} · estimados: {done.estimados} "
                f"· siguen sin dato: {done.sin_estimar}"
            )
            for method, count in sorted(done.por_metodo.items()):
                print(f"  {method}: {count}")
            print(
                "Guardado como ESTIMADO en gap_estimates."
                if done.guardado
                else "Simulación (--dry-run): no se guardó nada."
            )
            return 0
        if args.command == "import-siga-live":
            with create_session_factory(engine)() as session:
                repository = SqlIngestionRepository(session)
                live = SigaLiveImporter(
                    ImportService(repository, settings.data_cutoff_date),
                    repository,
                    SigaLiveClient(),
                    DEFAULT_DATA_DIR / "lluvia_diaria_siga_formosa.csv",
                    settings.data_cutoff_date,
                )
                mode = ImportMode.COMMIT if args.commit else ImportMode.AUDIT
                result = live.run(args.station, args.date_from, args.date_to, mode)
                if mode is ImportMode.COMMIT:
                    _recompute_flags(session)
            if result.origin == "respaldo_csv":
                print(f"AVISO: el SIGA en vivo no respondió ({result.reason}).")
                print("Se usó el CSV versionado de docs/datos/, no datos en vivo.")
            else:
                print("Origen: SIGA en vivo.")
            _print_report(result.report)
            return 0
        with create_session_factory(engine)() as session:
            service = ImportService(SqlIngestionRepository(session), settings.data_cutoff_date)
            content = args.file.read_bytes()
            if args.command == "import-stations":
                report = service.import_stations(args.source, args.file.name, content)
            else:
                mode = ImportMode.COMMIT if args.commit else ImportMode.AUDIT
                report = service.import_rainfall(args.source, args.file.name, content, mode)
                if mode is ImportMode.COMMIT:
                    _recompute_flags(session)
            _print_report(report)
    except (InvalidFileError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
