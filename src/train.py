"""
Model training and evaluation pipeline for HN HIT Predictor.
Trains a feature extraction and classification pipeline, evaluates metrics,
and saves the artifact for production serving.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)

from src.data_loader import load_or_create_dataset, enrich_features

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

FEATURE_COLUMNS = ["title", "domain_type", "submission_hour", "submission_day", "title_len", "title_word_count"]

def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "title_tfidf",
                TfidfVectorizer(
                    max_features=3000,
                    ngram_range=(1, 2),
                    stop_words="english",
                    sublinear_tf=True
                ),
                "title"
            ),
            (
                "domain_ohe",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["domain_type"]
            ),
            (
                "num_scaler",
                StandardScaler(),
                ["submission_hour", "submission_day", "title_len", "title_word_count"]
            )
        ]
    )

    clf = LogisticRegression(
        C=1.2,
        max_iter=1000,
        random_state=42,
        class_weight="balanced"
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", clf)
    ])
    return pipeline

def train_and_evaluate(force_synthetic: bool = False):
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = load_or_create_dataset(force_synthetic=force_synthetic)

    X = df[FEATURE_COLUMNS]
    y = df["is_hit"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples.")
    print("Fitting MLOps pipeline...")

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "test_samples": int(len(y_test)),
        "train_samples": int(len(y_train)),
    }

    print("\n--- Model Evaluation Results ---")
    for k, v in metrics.items():
        print(f"{k:>15}: {v}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, digits=4))

    # Save model artifact and metrics
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model artifact successfully saved to: {MODEL_PATH}")

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to: {METRICS_PATH}")

    return pipeline, metrics

if __name__ == "__main__":
    train_and_evaluate()
