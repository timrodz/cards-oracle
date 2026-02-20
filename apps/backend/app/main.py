import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.main import api_router
from app.core.config import app_settings
from app.core.embeddings_jobs import embeddings_job_service
from app.models.api import HealthCheckResponse

app = FastAPI(title="Card Oracle")

# Configure the logger
logger.add(
    sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>"
)

# Configure CORS
cors_origins = app_settings.cors_origins
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Configure a basic health-check endpoint
@app.get("/", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(Hello="World")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Load general instances here
    yield
    embeddings_job_service.shutdown()


app.include_router(api_router)
