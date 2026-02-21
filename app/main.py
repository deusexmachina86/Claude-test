from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import toilets


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Toilet Finder API",
    description="Find nearby public toilets using PostGIS geolocation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(toilets.router)


@app.get("/health")
def health():
    return {"status": "ok"}
