"""
Prediction Service for SupportIQ Predictive Support Intervention.
Loads trained models, scores live operational events, and generates explainable interventions.
Strictly conforms to Section 7 & Section 15 of README.md.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import joblib
import pandas as pd

from ai_engine.config import RiskLevel
from ai_engine.predictor.explainability import ExplainabilityEngine
from ai_engine.predictor.schemas import PredictionInput, PredictionResult
from ai_engine.predictor.train import (
    DEFAULT_ARTIFACT_PATH,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    train_and_save_models,
)


class PredictionEngine:
    """
    Inference service for customer support contact prediction
    and proactive intervention generation.
    """

    _bundle: Optional[Dict[str, Any]] = None

    @classmethod
    def _get_bundle(cls, artifact_path: Optional[Path] = None) -> Dict[str, Any]:
        """Lazy loader for model bundle."""
        if cls._bundle is not None:
            return cls._bundle

        path = Path(artifact_path) if artifact_path else DEFAULT_ARTIFACT_PATH
        if not path.exists():
            # If not yet trained, train on the fly
            train_and_save_models(artifact_path=path)

        cls._bundle = joblib.load(path)
        return cls._bundle

    @classmethod
    def predict(
        cls,
        data: Union[Dict[str, Any], PredictionInput],
        artifact_path: Optional[Path] = None,
    ) -> PredictionResult:
        """
        Calculates contact probability, likely issue category, and top reasons.

        Args:
            data: Dictionary or PredictionInput instance.
            artifact_path: Optional custom path to serialized artifact.

        Returns:
            PredictionResult matching README Section 15.
        """
        inp = data if isinstance(data, PredictionInput) else PredictionInput.model_validate(data)
        bundle = cls._get_bundle(artifact_path)

        # Prepare single-row DataFrame
        raw_features = {
            "delivery_delay": inp.delivery_delay,
            "previous_complaints": inp.previous_complaints,
            "courier_reliability": inp.courier_reliability,
            "warehouse_backlog": inp.warehouse_backlog,
            "order_value": inp.order_value,
            "payment_status": inp.payment_status,
            "product_category": inp.product_category,
            "cancellation_history": inp.cancellation_history,
        }

        feature_df = pd.DataFrame([raw_features])

        # 1. Binary Contact Probability
        contact_pipeline = bundle["contact_pipeline"]
        prob_classes = contact_pipeline.predict_proba(feature_df)[0]
        # Probability of class 1 (contact support)
        support_prob = float(prob_classes[1])
        support_prob_rounded = round(support_prob, 2)

        # 2. Issue Category Classification
        issue_pipeline = bundle["issue_pipeline"]
        issue_classes = bundle["issue_classes"]
        issue_probs_raw = issue_pipeline.predict_proba(feature_df)[0]
        issue_probs = {
            str(cls_name): round(float(p), 2)
            for cls_name, p in zip(issue_classes, issue_probs_raw)
        }
        predicted_issue = str(issue_pipeline.predict(feature_df)[0])

        # 3. Risk Level Determination
        if support_prob >= 0.70:
            risk_level = RiskLevel.HIGH.value
            recommended_intervention = "proactive_notification"
        elif support_prob >= 0.40:
            risk_level = RiskLevel.MEDIUM.value
            recommended_intervention = "proactive_notification"
        else:
            risk_level = RiskLevel.LOW.value
            recommended_intervention = "monitor_only"

        # 4. Reason Codes & Explainability
        reasons = ExplainabilityEngine.get_top_reasons(raw_features, max_reasons=3)

        return PredictionResult(
            customer_id=inp.customer_id,
            support_probability=support_prob_rounded,
            predicted_issue=predicted_issue,
            risk_level=risk_level,
            reasons=reasons,
            recommended_intervention=recommended_intervention,
            issue_probabilities=issue_probs,
        )
