from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pairo.api.webhook import router as webhook_router
from pairo.config import settings

app = FastAPI(title="Pairo", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.dashboard_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
