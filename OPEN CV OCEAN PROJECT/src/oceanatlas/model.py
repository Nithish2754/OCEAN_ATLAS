from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from .features import extract_frame_features

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]


class OceanVisionClassifier:
    def __init__(self, model=None, class_names=None):
        self.model = model or RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced_subsample",
            n_jobs=-1,
        )
        self.class_names = class_names or CLASS_NAMES
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray):
        if not self.is_fitted:
            raise ValueError("Classifier must be fitted before predicting.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray):
        if not self.is_fitted:
            raise ValueError("Classifier must be fitted before predicting probabilities.")
        return self.model.predict_proba(X)

    def save(self, model_path: str | Path):
        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as file:
            import joblib

            joblib.dump(self, file)

    @classmethod
    def load(cls, model_path: str | Path):
        import joblib

        return joblib.load(model_path)


def _collect_feature_rows(dataset_dir: str | Path):
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")

    features = []
    labels = []

    for class_dir in sorted(dataset_path.iterdir()):
        if not class_dir.is_dir() or class_dir.name not in CLASS_NAMES:
            continue

        for image_path in sorted(class_dir.glob("*.*")):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif"}:
                continue
            frame = cv2.imread(str(image_path))
            if frame is None:
                continue
            features.append(extract_frame_features(frame))
            labels.append(class_dir.name)

    if not features:
        raise ValueError(f"No valid images found in dataset directory: {dataset_path}")

    return np.vstack(features), np.asarray(labels)


def train_classifier(dataset_dir: str | Path, model_path: str | Path | None = None):
    X, y = _collect_feature_rows(dataset_dir)
    classifier = OceanVisionClassifier()
    classifier.fit(X, y)

    if model_path is not None:
        classifier.save(model_path)
    return classifier


def evaluate_classifier(dataset_dir: str | Path, model: OceanVisionClassifier | None = None):
    X, y = _collect_feature_rows(dataset_dir)
    if model is None:
        model = OceanVisionClassifier()
        model.fit(X, y)

    predictions = model.predict(X)
    matrix = confusion_matrix(y, predictions, labels=model.class_names)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y,
        predictions,
        labels=model.class_names,
        average=None,
        zero_division=0,
    )
    metrics = {
        "confusion_matrix": matrix.tolist(),
        "labels": model.class_names,
        "precision": {label: float(score) for label, score in zip(model.class_names, precision)},
        "recall": {label: float(score) for label, score in zip(model.class_names, recall)},
        "f1_score": {label: float(score) for label, score in zip(model.class_names, f1)},
    }
    return metrics


def classify_frame(frame: np.ndarray, classifier: OceanVisionClassifier):
    feature_vector = extract_frame_features(frame)
    prediction = classifier.predict(feature_vector.reshape(1, -1))[0]
    probabilities = classifier.predict_proba(feature_vector.reshape(1, -1))[0]
    confidence = float(np.max(probabilities))
    return prediction, confidence


def train_and_split(dataset_dir: str | Path, test_size: float = 0.2, random_state: int = 42):
    X, y = _collect_feature_rows(dataset_dir)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    classifier = OceanVisionClassifier()
    classifier.fit(X_train, y_train)
    return classifier, X_test, y_test


def save_metrics_json(metrics: dict, output_path: str | Path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
