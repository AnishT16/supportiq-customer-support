"""
Model Training Pipeline for Predictive Support Intervention.
Trains binary contact probability classifier and multiclass issue category classifier.
Serializes trained pipelines with joblib.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ai_engine.predictor.dataset import generate_synthetic_support_data

NUMERICAL_FEATURES = [
    "delivery_delay",
    "previous_complaints",
    "courier_reliability",
    "order_value",
    "cancellation_history",
]

CATEGORICAL_FEATURES = [
    "warehouse_backlog",
    "payment_status",
    "product_category",
]

DEFAULT_ARTIFACT_DIR = Path(__file__).parent / "artifacts"
DEFAULT_ARTIFACT_PATH = DEFAULT_ARTIFACT_DIR / "predictor_model.joblib"


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def train_and_save_models(
    artifact_path: Optional[Path] = None,
    n_samples: int = 3500,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Generates training data, trains the dual classification models,
    evaluates performance, and serializes artifacts.
    """
    save_path = Path(artifact_path) if artifact_path else DEFAULT_ARTIFACT_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate dataset
    df = generate_synthetic_support_data(n_samples=n_samples, random_state=random_state)

    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y_contact = df["contact_support"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_contact, test_size=0.2, random_state=random_state, stratify=y_contact
    )

    # 2. Train Binary Contact Classifier
    contact_pipeline = Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=7,
                    min_samples_leaf=3,
                    random_state=random_state,
                ),
            ),
        ]
    )
    contact_pipeline.fit(X_train, y_train)

    # Evaluate contact classifier
    contact_probs = contact_pipeline.predict_proba(X_test)[:, 1]
    roc_auc = float(roc_auc_score(y_test, contact_probs))

    # 3. Train Multiclass Issue Classifier on contacted subset
    df_contacted = df[df["contact_support"] == 1]
    X_issue = df_contacted[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y_issue = df_contacted["issue_category"]

    issue_pipeline = Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=8,
                    random_state=random_state,
                ),
            ),
        ]
    )
    issue_pipeline.fit(X_issue, y_issue)

    # 4. Serialize Model Artifacts
    bundle = {
        "contact_pipeline": contact_pipeline,
        "issue_pipeline": issue_pipeline,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "issue_classes": list(issue_pipeline.classes_),
        "roc_auc": roc_auc,
    }

    joblib.dump(bundle, save_path)

    return {
        "status": "success",
        "artifact_path": str(save_path),
        "roc_auc": roc_auc,
        "issue_classes": list(issue_pipeline.classes_),
    }


if __name__ == "__main__":
    result = train_and_save_models()
    print("Model training completed successfully!")
    print(f"Artifact saved at: {result['artifact_path']}")
    print(f"Validation ROC-AUC: {result['roc_auc']:.4f}")
    print(f"Available Issue Categories: {result['issue_classes']}")
