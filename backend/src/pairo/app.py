from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pairo.config import settings

app = FastAPI(title="Pairo", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.dashboard_origin],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
