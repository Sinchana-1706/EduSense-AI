"""
EduSense AI FastAPI Application Entry Point.
"""

import sys
import os
from contextlib import asynccontextmanager

# Ensure backend directory (containing `ai` and `database` packages) is first on Python path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.routers.health import router as health_router
from app.routers.students import router as students_router
from app.routers.livekit import router as livekit_router
from app.routers.attendance import router as attendance_router
from app.routers.emotion import router as emotion_router
from app.routers.speech import router as speech_router
from app.routers.sentiment import router as sentiment_router
from app.routers.classrooms import router as classrooms_router
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Initializes database tables on application startup.
    """
    try:
        init_db()
        print("[DB] Database connection initialized and tables verified.")
    except Exception as e:
        err_msg = str(e).encode("ascii", "ignore").decode("ascii")
        print(f"[DB Notice] Database initialization notice: {err_msg}")
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
app.include_router(livekit_router)
app.include_router(attendance_router)
app.include_router(emotion_router)
app.include_router(speech_router)
app.include_router(sentiment_router)
app.include_router(classrooms_router)


@app.get("/", summary="Root Endpoint")
def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME} Backend API",
        "health_check": "/health",
        "students_api": "/api/v1/students",
        "classrooms_api": "/api/v1/classrooms",
        "livekit_api": "/api/v1/livekit/token",
        "attendance_api": "/api/v1/attendance",
        "emotion_api": "/api/v1/emotion",
        "speech_api": "/api/v1/speech",
        "sentiment_api": "/api/v1/sentiment",
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
