from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = BASE_DIR / "model" / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"


class InferenceService:
    def __init__(self) -> None:
        if not MODEL_PATH.exists() or not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Model artifacts not found. Run: python model/train.py"
            )

        self.model = joblib.load(MODEL_PATH)
        self.metadata = json.loads(METADATA_PATH.read_text())

        self.threshold: float = float(self.metadata["threshold"])
        self.features: list[str] = list(self.metadata["features"])

    def model_info(self) -> Dict[str, Any]:
        return self.metadata

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # enforce feature ordering
        df = pd.DataFrame([payload])[self.features]

        prob = float(self.model.predict_proba(df)[0, 1])
        label = int(prob >= self.threshold)

        return {
            "probability": prob,
            "label": label,
            "model_version": self.metadata["created_utc"],
            "threshold": self.threshold,
        }


# Singleton instance loaded once
service = InferenceService()

