import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.main import api_router
from app.core.config import app_settings, db_settings
from app.models.api import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application: connecting to MongoDB.")
    uri = db_settings.uri.encoded_string()
    mongo_client: MongoClient = MongoClient(uri)
    app.state.mongo_client = mongo_client
    yield
    logger.info("Shutting down application: closing MongoDB connection.")
    mongo_client.close()


app = FastAPI(title="Card Oracle", lifespan=lifespan)

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


app.include_router(api_router)
