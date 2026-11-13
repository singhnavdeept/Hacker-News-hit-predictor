import os
import pytest
import pandas as pd
from src.train import train_and_evaluate, MODEL_PATH, METRICS_PATH
from src.data_loader import extract_domain_type

def test_extract_domain_type():
    assert extract_domain_type("https://github.com/fastapi/fastapi") == "github"
    assert extract_domain_type("https://techcrunch.com/article-123") == "tech_media"
    assert extract_domain_type("https://arxiv.org/abs/2401.0001") == "paper"
    assert extract_domain_type("") == "self"
    assert extract_domain_type(None) == "self"

def test_model_training_and_artifacts():
    # Force synthetic benchmark dataset for quick reproducible test
    pipeline, metrics = train_and_evaluate(force_synthetic=True)
    assert os.path.exists(MODEL_PATH)
    assert os.path.exists(METRICS_PATH)
    assert metrics["accuracy"] >= 0.70
    assert metrics["roc_auc"] >= 0.75

def test_model_inference():
    import joblib
    model = joblib.load(MODEL_PATH)

    test_df = pd.DataFrame([{
        "title": "Show HN: RustKV – High performance distributed cache",
        "domain_type": "github",
        "submission_hour": 15,
        "submission_day": 2,
        "title_len": 54,
        "title_word_count": 8
    }])

    prob = model.predict_proba(test_df)[0, 1]
    assert 0.0 <= prob <= 1.0
