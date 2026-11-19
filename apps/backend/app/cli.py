"""Línea de comandos: `python -m app.cli --help`.

Importar es una acción de quien administra la base; no se expone por la API pública.
"""

import argparse
import sys
from pathlib import Path

from app.config import get_settings
from app.db.session import create_db_engine, create_session_factory
from app.domain.enums import ImportMode
from app.ingestion.types import ImportReport, InvalidFileError
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.quality import SqlQualityRepository
from app.services.importer import ImportService
from app.services.quality import QualityService


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

    commands.add_parser("recompute-flags", help="Recalcula las banderas de calidad")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    engine = create_db_engine(settings.database_url)
    try:
        if args.command == "recompute-flags":
            with create_session_factory(engine)() as session:
                counts = QualityService(SqlQualityRepository(session)).recompute_zero_streaks()
            print(
                f"Estaciones revisadas: {len(counts)} · "
                f"tramos de ceros prolongados: {sum(counts.values())}"
            )
            return 0
        with create_session_factory(engine)() as session:
            service = ImportService(SqlIngestionRepository(session), settings.data_cutoff_date)
            content = args.file.read_bytes()
            if args.command == "import-stations":
                report = service.import_stations(args.source, args.file.name, content)
            else:
                mode = ImportMode.COMMIT if args.commit else ImportMode.AUDIT
                report = service.import_rainfall(args.source, args.file.name, content, mode)
            _print_report(report)
    except (InvalidFileError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
