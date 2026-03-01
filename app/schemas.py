from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    income: float = Field(..., ge=0)
    age: float = Field(..., ge=0, le=120)
    debt_ratio: float = Field(..., ge=0, le=1)
    credit_score: float = Field(..., ge=0, le=1000)
    loan_amount: float = Field(..., ge=0)
    employment_years: float = Field(..., ge=0, le=60)


class PredictResponse(BaseModel):
    probability: float
    label: int
    model_version: str
    threshold: float


class HealthResponse(BaseModel):
    status: str = "ok"


class ModelInfoResponse(BaseModel):
    model_type: str
    created_utc: str
    seed: int
    n_samples: int
    threshold: float
    features: list[str]
    metrics: dict
    deps: dict

