"""Reinicio de la base de demo: borra la base SQLite y la vuelve a cargar desde `docs/datos/`.

Funciona sin conexión. Solo toca un archivo SQLite local: nunca una base de otro motor.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.db.session import create_db_engine, create_session_factory
from app.domain.enums import ImportMode
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.quality import SqlQualityRepository
from app.services.importer import ImportService
from app.services.quality import QualityService

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BACKEND_DIR.parents[1] / "docs" / "datos"
STATIONS_FILE = "estaciones_siga_formosa.csv"
RAINFALL_FILE = "lluvia_diaria_siga_formosa.csv"
SOURCE = "siga_inta"


class DemoResetError(Exception):
    """Algo impide reiniciar la demo; el mensaje se muestra tal cual."""


@dataclass(frozen=True)
class DemoResult:
    database: Path
    stations: int
    rainfall_rows: int
    rejected_rows: int
    zero_streaks: int


def sqlite_file(database_url: str) -> Path:
    """El archivo de una base SQLite. Cualquier otra cosa se rechaza antes de borrar nada."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise DemoResetError(
            "El reinicio solo funciona con una base SQLite local; "
            f"DATABASE_URL usa «{url.drivername}». No se tocó nada."
        )
    if not url.database or url.database == ":memory:":
        raise DemoResetError("La base es temporal (en memoria): no hay nada que reiniciar.")
    return Path(url.database).resolve()


def _migrate(database_url: str) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def reset_demo(
    database_url: str,
    cutoff: date,
    confirm: Callable[[Path], bool],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> DemoResult | None:
    """Devuelve None si quien administra no confirma. Los datos se revisan antes de borrar."""
    database = sqlite_file(database_url)
    stations_csv = data_dir / STATIONS_FILE
    rainfall_csv = data_dir / RAINFALL_FILE
    missing = [p.name for p in (stations_csv, rainfall_csv) if not p.is_file()]
    if missing:
        raise DemoResetError(
            f"Faltan los datos versionados en {data_dir}: {', '.join(missing)}. No se borró nada."
        )
    if not confirm(database):
        return None

    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{database}{suffix}").unlink(missing_ok=True)
    database.parent.mkdir(parents=True, exist_ok=True)
    _migrate(database_url)

    engine = create_db_engine(database_url)
    try:
        with create_session_factory(engine)() as session:
            service = ImportService(SqlIngestionRepository(session), cutoff)
            stations = service.import_stations(SOURCE, stations_csv.name, stations_csv.read_bytes())
            rainfall = service.import_rainfall(
                SOURCE, rainfall_csv.name, rainfall_csv.read_bytes(), ImportMode.COMMIT
            )
            streaks = QualityService(SqlQualityRepository(session)).recompute_zero_streaks()
    finally:
        engine.dispose()
    return DemoResult(
        database=database,
        stations=stations.rows_accepted,
        rainfall_rows=rainfall.rows_accepted,
        rejected_rows=rainfall.rows_rejected + stations.rows_rejected,
        zero_streaks=sum(streaks.values()),
    )
