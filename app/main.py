from __future__ import annotations

from fastapi import FastAPI

from app.inference import service
from app.schemas import HealthResponse, ModelInfoResponse, PredictRequest, PredictResponse

app = FastAPI(
    title="Cloud-Native ML Inference API",
    version="0.1.0",
    description="A container-ready inference service backed by a reproducible sklearn model.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> dict:
    return service.model_info()


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> dict:
    return service.predict(req.model_dump())

