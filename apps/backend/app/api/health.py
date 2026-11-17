from fastapi import APIRouter, Depends

from app import __version__
from app.config import Settings, get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["sistema"])


@router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:  # noqa: B008
    return HealthResponse(
        status="ok",
        version=__version__,
        env=settings.app_env,
        data_cutoff_date=settings.data_cutoff_date,
    )
