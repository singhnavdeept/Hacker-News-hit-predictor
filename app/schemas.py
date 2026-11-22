from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300, json_schema_extra={"example": "Show HN: RustKV – A high performance key-value store"})
    url: Optional[str] = Field(None, json_schema_extra={"example": "https://github.com/example/rustkv"})
    submission_time: Optional[str] = Field(None, description="ISO format date-time string, e.g. 2026-11-08T15:30:00Z")

class PredictionResponse(BaseModel):
    title: str
    is_hit: bool
    hit_probability: float
    confidence_level: str
    prediction_label: str
    features: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
    version: str

class MetricsResponse(BaseModel):
    status: str
    metrics: Dict[str, Any]

class VersionResponse(BaseModel):
    service: str
    version: str
    git_sha: str
    environment: str
    model_loaded: bool
    timestamp: str
