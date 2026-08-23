from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.database import router as database_router
from app.api.ingestion import router as ingestion_router
from app.api.intelligence import router as intelligence_router
from app.api.validation import router as validation_router
from app.api.export import router as export_router
from app.api.enrichment import router as enrichment_router
from app.api.query import router as query_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(database_router, prefix=settings.API_PREFIX)
app.include_router(ingestion_router, prefix=settings.API_PREFIX)
app.include_router(intelligence_router, prefix=settings.API_PREFIX)
app.include_router(validation_router, prefix=settings.API_PREFIX)
app.include_router(export_router, prefix=settings.API_PREFIX)
app.include_router(enrichment_router, prefix=settings.API_PREFIX)
app.include_router(query_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "project": "Deadlock",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }
