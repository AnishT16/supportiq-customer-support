"""
Unit Tests for Predictive Support Intervention Engine.
Verifies dataset generation, training pipeline, inference service, and explainability.
"""

from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from ai_engine.config import RiskLevel
from ai_engine.predictor.dataset import generate_synthetic_support_data
from ai_engine.predictor.explainability import ExplainabilityEngine
from ai_engine.predictor.inference import PredictionEngine
from ai_engine.predictor.schemas import PredictionInput
from ai_engine.predictor.train import train_and_save_models


def test_synthetic_dataset_generation():
    """Verify synthetic dataset shapes and column distribution."""
    df = generate_synthetic_support_data(n_samples=500, random_state=42)
    assert len(df) == 500
    expected_cols = [
        "customer_id",
        "delivery_delay",
        "previous_complaints",
        "courier_reliability",
        "warehouse_backlog",
        "order_value",
        "payment_status",
        "product_category",
        "cancellation_history",
        "contact_support",
        "issue_category",
    ]
    for col in expected_cols:
        assert col in df.columns


def test_model_training_pipeline(tmp_path):
    """Test model training and artifact serialization."""
    artifact_file = tmp_path / "test_model.joblib"
    result = train_and_save_models(artifact_path=artifact_file, n_samples=600)

    assert result["status"] == "success"
    assert result["roc_auc"] >= 0.70
    assert artifact_file.exists()


def test_prediction_high_risk_delivery_delay():
    """
    Simulates the exact example from README Section 7:
    Customer 9281, 3 day delay, 2 complaints, low courier reliability, high backlog.
    Should output HIGH risk and recommended proactive intervention.
    """
    input_data = {
        "customer_id": 9281,
        "delivery_delay": 3.0,
        "previous_complaints": 2,
        "courier_reliability": 0.55,
        "warehouse_backlog": "High",
        "order_value": 4800.0,
        "payment_status": "PAID",
        "product_category": "Electronics",
        "cancellation_history": 0,
    }

    result = PredictionEngine.predict(input_data)

    assert result.customer_id == 9281
    assert result.support_probability >= 0.70
    assert result.risk_level == RiskLevel.HIGH.value
    assert result.recommended_intervention == "proactive_notification"
    assert any("delivery delay" in r for r in result.reasons)
    assert any("complaint" in r for r in result.reasons)


def test_prediction_low_risk_smooth_order():
    """
    Order with zero delay, high courier reliability, and no prior complaints
    should be evaluated as LOW risk with monitor_only.
    """
    input_data = PredictionInput(
        customer_id=1040,
        delivery_delay=0.0,
        previous_complaints=0,
        courier_reliability=0.98,
        warehouse_backlog="Low",
        order_value=75.0,
        payment_status="PAID",
        product_category="Books",
        cancellation_history=0,
    )

    result = PredictionEngine.predict(input_data)

    assert result.customer_id == 1040
    assert result.support_probability <= 0.45
    assert result.risk_level == RiskLevel.LOW.value
    assert result.recommended_intervention == "monitor_only"


def test_explainability_reason_extraction():
    """Test explainability engine prioritizes the most influential signals."""
    features = {
        "delivery_delay": 3.0,
        "previous_complaints": 2,
        "warehouse_backlog": "High",
        "courier_reliability": 0.60,
    }
    reasons = ExplainabilityEngine.get_top_reasons(features, max_reasons=3)
    assert len(reasons) <= 3
    assert any("3 day delivery delay" in r for r in reasons)
    assert any("previous complaints" in r for r in reasons)


def test_prediction_to_dict_matches_readme_spec():
    """
    Verify dictionary serialization conforms to README Section 15 contract:
    {
      "customer_id": 9281,
      "support_probability": 0.91,
      "predicted_issue": "delivery_delay",
      "risk_level": "HIGH",
      "reasons": [...],
      "recommended_intervention": "proactive_notification"
    }
    """
    input_data = {
        "customer_id": 9281,
        "delivery_delay": 3.0,
        "previous_complaints": 2,
        "courier_reliability": 0.65,
        "warehouse_backlog": "High",
        "order_value": 1200.0,
    }

    result = PredictionEngine.predict(input_data)
    d = result.to_dict()

    required_keys = [
        "customer_id",
        "support_probability",
        "predicted_issue",
        "risk_level",
        "reasons",
        "recommended_intervention",
    ]
    for key in required_keys:
        assert key in d, f"Missing key '{key}' in prediction response"
    assert d.get("prediction_window") == "next_48_hours"


def test_prediction_input_validation_bounds():
    """Verify out-of-bounds inputs raise descriptive validation errors."""
    import pytest
    from pydantic import ValidationError

    # Negative delivery delay
    with pytest.raises(ValidationError):
        PredictionInput(customer_id=1, delivery_delay=-2.0)

    # Courier reliability > 1.0
    with pytest.raises(ValidationError):
        PredictionInput(customer_id=1, courier_reliability=1.5)

    # Negative order value
    with pytest.raises(ValidationError):
        PredictionInput(customer_id=1, order_value=-50.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

