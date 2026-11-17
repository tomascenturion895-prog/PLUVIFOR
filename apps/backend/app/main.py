from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health, series, stations
from app.config import Settings, get_settings
from app.db.session import create_db_engine, create_session_factory
from app.errors import register_error_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="PLUVIFOR · API",
        version=__version__,
        description=(
            "Reporte pluvial de Formosa. "
            "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial."
        ),
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.state.engine = create_db_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(stations.router)
    app.include_router(series.router)
    return app


app = create_app()
