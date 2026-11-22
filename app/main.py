import os
import sys
import json
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    MetricsResponse,
    VersionResponse
)
from src.data_loader import extract_domain_type

# ----------------------------------------------------------------------
# Structured JSON Logging for CloudWatch Metric Filters & Ingestion
# ----------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, "props"):
            log_entry.update(record.props)
        return json.dumps(log_entry)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("hn-hit-predictor")
logger.setLevel(logging.INFO)
logger.handlers = [handler]
logger.propagate = False

# Model and artifact paths
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model.joblib")
METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "metrics.json")

# Metadata injected by Docker build & environment
GIT_COMMIT = os.getenv("GIT_COMMIT", "dev-local")
APP_ENV = os.getenv("ENV", "development")
APP_VERSION = "1.0.0"

model_pipeline = None
model_metrics = {}

def load_model():
    global model_pipeline, model_metrics
    if os.path.exists(MODEL_PATH):
        logger.info(f"Loading trained model from {MODEL_PATH}")
        model_pipeline = joblib.load(MODEL_PATH)
    else:
        logger.warning(f"Model file not found at {MODEL_PATH}. Prediction requests will fail until trained.")

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            model_metrics = json.load(f)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield

app = FastAPI(
    title="HN HIT Predictor API",
    description="MLOps Inference Service for predicting whether a Hacker News post will reach the front page.",
    version=APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware for CloudWatch JSON ingestion
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    client_host = request.client.host if request.client else "unknown"
    
    # Structured JSON log entry
    log_record = logging.LogRecord(
        name="hn-hit-predictor",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"{request.method} {request.url.path} returned {response.status_code} in {duration_ms}ms",
        args=(),
        exc_info=None
    )
    log_record.props = {
        "service": "hn-hit-predictor",
        "environment": APP_ENV,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": duration_ms,
        "client_ip": client_host
    }
    logger.handle(log_record)
    
    return response

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", tags=["UI"])
def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "project": "HN HIT Predictor",
        "description": "MLOps Pipeline on AWS / Docker",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "predict": "/predict",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="healthy",
        service="hn-hit-predictor-api",
        model_loaded=(model_pipeline is not None),
        version=APP_VERSION
    )

@app.get("/version", response_model=VersionResponse, tags=["Deploy Verification"])
def get_version():
    """Returns deployment version, Git SHA, and environment for CI/CD deploy verification."""
    return VersionResponse(
        service="hn-hit-predictor-api",
        version=APP_VERSION,
        git_sha=GIT_COMMIT,
        environment=APP_ENV,
        model_loaded=(model_pipeline is not None),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
def get_metrics():
    return MetricsResponse(
        status="success",
        metrics=model_metrics if model_metrics else {"message": "Model not yet evaluated"}
    )

@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_hit(payload: PredictionRequest):
    if model_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Please train or deploy the model artifact first."
        )

    # Parse submission time
    if payload.submission_time:
        try:
            dt = datetime.fromisoformat(payload.submission_time.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    submission_hour = dt.hour
    submission_day = dt.weekday()
    domain_type = extract_domain_type(payload.url or "")
    title_clean = payload.title.strip()
    title_len = len(title_clean)
    title_word_count = len(title_clean.split())

    feature_dict = {
        "title": title_clean,
        "domain_type": domain_type,
        "submission_hour": submission_hour,
        "submission_day": submission_day,
        "title_len": title_len,
        "title_word_count": title_word_count
    }

    df_input = pd.DataFrame([feature_dict])

    try:
        # Predict class and probability
        prob = float(model_pipeline.predict_proba(df_input)[0, 1])
        is_hit = bool(prob >= 0.50)

        if prob >= 0.70:
            confidence = "High"
        elif prob >= 0.40:
            confidence = "Medium"
        else:
            confidence = "Low"

        label = "Likely Hit (Frontpage Material)" if is_hit else "Unlikely Hit"

        return PredictionResponse(
            title=title_clean,
            is_hit=is_hit,
            hit_probability=round(prob, 4),
            confidence_level=confidence,
            prediction_label=label,
            features=feature_dict
        )
    except Exception as exc:
        logger.error(f"Prediction error: {exc}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(exc)}")
