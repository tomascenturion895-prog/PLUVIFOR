from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import (
    alerts,
    auth,
    events,
    field_reports,
    gap_estimates,
    health,
    imports,
    network_health,
    rainfall,
    recurrence,
    references,
    reports,
    sensor_readings,
    stations,
)
from app.config import Settings, get_settings
from app.db.session import create_db_engine, create_session_factory
from app.errors import register_error_handlers
from app.security import BodySizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware


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
    # Lo último que se agrega es lo más externo: primero se limita el tamaño y las
    # respuestas, incluidos los errores, salen con los encabezados de seguridad.
    app.add_middleware(
        BodySizeLimitMiddleware,
        default=settings.max_request_bytes,
        limits=(("/api/import", settings.max_upload_bytes + 1024),),
    )
    app.add_middleware(
        RateLimitMiddleware,
        default=settings.rate_limit_per_minute,
        limits=(
            ("/api/import", settings.rate_limit_import_per_minute),
            ("/api/auth", settings.rate_limit_auth_per_minute),
        ),
    )
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.app_env == "production")
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(stations.router)
    app.include_router(network_health.router)
    app.include_router(rainfall.router)
    app.include_router(field_reports.router)
    app.include_router(gap_estimates.router)
    app.include_router(sensor_readings.router)
    app.include_router(imports.router)
    app.include_router(reports.router)
    app.include_router(recurrence.router)
    app.include_router(events.router)
    app.include_router(alerts.router)
    app.include_router(auth.router)
    app.include_router(auth.users_router)
    app.include_router(references.router)
    return app


app = create_app()
