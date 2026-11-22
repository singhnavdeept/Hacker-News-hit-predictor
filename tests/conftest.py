import os
import pytest
from src.train import train_and_evaluate, MODEL_PATH

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure trained model artifact exists for API and integration tests."""
    if not os.path.exists(MODEL_PATH):
        print("\n[conftest] Training test model artifact for test suite...")
        train_and_evaluate(force_synthetic=True)
    yield
