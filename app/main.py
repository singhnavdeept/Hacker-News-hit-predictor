import os
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictionRequest, PredictionResponse, HealthResponse, MetricsResponse
from src.data_loader import extract_domain_type

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hn-hit-predictor")

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model.joblib")
METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "metrics.json")

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
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Info"])
def root():
    return {
        "project": "HN HIT Predictor",
        "description": "MLOps Pipeline on AWS / Docker",
        "endpoints": {
            "health": "/health",
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
        version="1.0.0"
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
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()

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

        logger.info(f"Prediction made for '{title_clean}' -> Hit: {is_hit} (prob={prob:.3f})")

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
