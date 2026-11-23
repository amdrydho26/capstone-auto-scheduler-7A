import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.api.router import api_router
from app.services.data_loader import seed_data_from_csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed CSV Data from data/ folder
    # Lokasi folder data relatif terhadap root proyek
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(base_dir, "data")

    db = SessionLocal()
    try:
        seed_data_from_csv(db, data_dir)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": "1.0.0",
        "status": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
