"""
EduSense AI FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.routers.health import router as health_router
from app.routers.students import router as students_router
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Initializes database tables on application startup.
    """
    try:
        init_db()
        print("✅ Database connection initialized and tables verified.")
    except Exception as e:
        print(f"⚠️ Database initialization warning (Verify PostgreSQL service is active): {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Online Classroom Analytics System - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware for Frontend Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health_router)
app.include_router(students_router)


@app.get("/", summary="Root Endpoint")
def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME} Backend API",
        "health_check": "/health",
        "students_api": "/api/v1/students",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
