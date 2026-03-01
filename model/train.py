from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ---------
# Config
# ---------
SEED = 42
N_SAMPLES = 15000
THRESHOLD = 0.50

FEATURES: List[str] = [
    "income",
    "age",
    "debt_ratio",
    "credit_score",
    "loan_amount",
    "employment_years",
]

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"


@dataclass
class Metadata:
    model_type: str
    created_utc: str
    seed: int
    n_samples: int
    threshold: float
    features: List[str]
    metrics: dict
    deps: dict


def make_synthetic_dataset(n: int, seed: int) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generate a synthetic but realistic-looking tabular dataset.

    Key idea:
    - We create features with plausible ranges
    - Then we create a hidden 'risk score' (linear-ish)
    - Then we convert it into probability via sigmoid
    - Then sample binary labels
    """
    rng = np.random.default_rng(seed)

    # Feature distributions (chosen for realism, not "truth")
    income = rng.normal(loc=45000, scale=18000, size=n).clip(15000, 200000)
    age = rng.normal(loc=35, scale=10, size=n).clip(18, 75)
    debt_ratio = rng.beta(a=2.0, b=5.0, size=n).clip(0.0, 1.0)  # 0..1
    credit_score = rng.normal(loc=680, scale=70, size=n).clip(300, 850)
    loan_amount = rng.normal(loc=12000, scale=8000, size=n).clip(500, 60000)
    employment_years = rng.normal(loc=5, scale=4, size=n).clip(0, 40)

    X = pd.DataFrame(
        {
            "income": income,
            "age": age,
            "debt_ratio": debt_ratio,
            "credit_score": credit_score,
            "loan_amount": loan_amount,
            "employment_years": employment_years,
        }
    )

    # Hidden risk score (this is the synthetic "ground truth")
    # Higher debt_ratio & loan_amount -> higher risk
    # Higher credit_score & income & employment_years -> lower risk
    score = (
        1.6 * debt_ratio
        + 0.00006 * loan_amount
        - 0.00002 * income
        - 0.004 * (credit_score - 650)
        - 0.02 * employment_years
        + 0.01 * (age - 35)
    )

    # Add some noise so it isn't perfectly separable
    score += rng.normal(0, 0.25, size=n)

    # Convert score -> probability via sigmoid
    prob = 1 / (1 + np.exp(-score))

    # Sample labels using the probability
    y = rng.binomial(n=1, p=prob, size=n).astype(int)

    return X[FEATURES], y


def train_model(X: pd.DataFrame, y: np.ndarray, seed: int) -> Pipeline:
    """
    Train a simple, stable model suitable for inference serving.
    We use a sklearn Pipeline so preprocessing + model stays together.
    """
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=200, random_state=seed)),
        ]
    )
    pipeline.fit(X, y)
    return pipeline


def evaluate(model: Pipeline, X_test: pd.DataFrame, y_test: np.ndarray) -> dict:
    """
    Produce metrics we can store in metadata for traceability.
    """
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= THRESHOLD).astype(int)

    return {
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "accuracy": float(accuracy_score(y_test, preds)),
    }


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    X, y = make_synthetic_dataset(N_SAMPLES, SEED)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    model = train_model(X_train, y_train, SEED)
    metrics = evaluate(model, X_test, y_test)

    # Save model artifact
    joblib.dump(model, MODEL_PATH)

    # Save metadata
    meta = Metadata(
      model_type="sklearn.pipeline(StandardScaler + LogisticRegression)",
      created_utc=datetime.now(timezone.utc).isoformat(),
      seed=SEED,
      n_samples=N_SAMPLES,
      threshold=THRESHOLD,
      features=FEATURES,
      metrics=metrics,
      deps={
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
      },
    )
    METADATA_PATH.write_text(json.dumps(asdict(meta), indent=2))

    print("✅ Training complete")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")
    print("Metrics:", metrics)


if __name__ == "__main__":
    main()
