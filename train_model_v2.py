"""Safe retraining for the medical-device XGBoost risk model.

This script is intentionally conservative:
- it keeps XGBoost as the real model,
- fixes the target mapping so Class 3 / III is the positive High Risk class,
- removes unknown action_classification rows instead of treating them as low risk,
- uses scale_pos_weight for imbalance,
- optionally adds probability calibration to improve probability realism,
- evaluates both ROC-AUC and PR-AUC,
- prints a probability distribution summary and example records,
- saves the final sklearn pipeline to backend/ml/medical_device_xgboost_13features_v2.pkl.

The resulting saved object is compatible with the existing FastAPI model service,
which calls model.predict() and model.predict_proba().
"""

from __future__ import annotations

import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
MODEL_PATH = ROOT_DIR / "backend" / "ml" / "medical_device_xgboost_13features_v2.pkl"

FEATURE_COLUMNS = [
    "type",
    "status",
    "classification",
    "risk_class",
    "country_event",
    "country_device",
    "implanted",
    "name_manufacturer",
    "quantity_in_commerce",
    "event_count",
    "manufacturer_event_count",
    "event_year",
    "event_month",
]

CATEGORICAL_COLUMNS = [
    "type",
    "status",
    "classification",
    "risk_class",
    "country_event",
    "country_device",
    "implanted",
    "name_manufacturer",
]

NUMERICAL_COLUMNS = [
    "quantity_in_commerce",
    "event_count",
    "manufacturer_event_count",
    "event_year",
    "event_month",
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_class_label(value):
    """Normalize labels so 'Class I', 'I', 'Class 1', etc. are all consistent."""
    if pd.isna(value):
        return ""
    token = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return token


def assign_target(action_classification):
    """Map action classification to the binary target.

    Safe mapping used here:
    - Class 1 / Class I / I / 1 => 0 (Low Risk)
    - Class 2 / Class II / II / 2 => 0 (Low Risk)
    - Class 3 / Class III / III / 3 => 1 (High Risk)
    - Voluntary recall -> 1 (High Risk) if present
    - Unknown values are dropped, not treated as low risk.
    """
    norm = normalize_class_label(action_classification)
    if not norm:
        return np.nan

    high_risk_values = {"CLASS3", "CLASSIII", "III", "3", "VOLUNTARYRECALL"}
    low_risk_values = {"CLASS1", "CLASSI", "I", "1", "CLASS2", "CLASSII", "II", "2"}

    if norm in high_risk_values:
        return 1
    if norm in low_risk_values:
        return 0
    return np.nan


def load_and_merge_data():
    """Load the three dataset files and merge them in the same way as the app uses them."""
    devices = pd.read_csv(DATA_DIR / "devices-1681209661.csv", low_memory=False)
    events = pd.read_csv(DATA_DIR / "events-1681209680.csv", low_memory=False)
    manufacturers = pd.read_csv(DATA_DIR / "manufacturers-1681209657.csv", low_memory=False)

    print(f"Devices rows: {len(devices):,}")
    print(f"Events rows: {len(events):,}")
    print(f"Manufacturers rows: {len(manufacturers):,}")

    # keep only the join keys and the necessary columns
    devices_subset = devices[[
        "id",
        "manufacturer_id",
        "classification",
        "implanted",
        "country",
        "name",
        "quantity_in_commerce",
        "risk_class",
    ]].copy()
    devices_subset = devices_subset.rename(columns={
        "id": "device_id",
        "country": "country_device",
        "name": "device_name",
    })

    manufacturers_subset = manufacturers[["id", "name"]].copy()
    manufacturers_subset = manufacturers_subset.rename(columns={
        "id": "manufacturer_id",
        "name": "name_manufacturer",
    })

    merged = events[["device_id", "type", "status", "country", "action_classification", "date"]].merge(
        devices_subset,
        on="device_id",
        how="inner",
    )

    merged = merged.merge(
        manufacturers_subset,
        on="manufacturer_id",
        how="left",
    )

    merged["date_parsed"] = pd.to_datetime(merged["date"], errors="coerce")
    merged["event_year"] = merged["date_parsed"].dt.year
    merged["event_month"] = merged["date_parsed"].dt.month

    device_event_counts = merged.groupby("device_id").size().rename("event_count")
    manufacturer_event_counts = merged.groupby("manufacturer_id").size().rename("manufacturer_event_count")

    merged = merged.merge(device_event_counts, on="device_id", how="left")
    merged = merged.merge(manufacturer_event_counts, on="manufacturer_id", how="left")

    # keep the canonical feature names
    merged = merged.rename(columns={"country_x": "country_event", "country_y": "country_device"})
    if "country" in merged.columns:
        merged = merged.rename(columns={"country": "country_event"})

    # clean strings
    for col in CATEGORICAL_COLUMNS:
        if col in merged.columns:
            merged[col] = merged[col].map(clean_text)

    # force known missing categories to a constant token instead of blank strings
    for col in CATEGORICAL_COLUMNS:
        if col in merged.columns:
            merged[col] = merged[col].replace({"": "Unknown"})

    for col in NUMERICAL_COLUMNS:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

    return merged


def build_feature_frame(df):
    """Create the exact 13-feature frame expected by the FastAPI model service."""
    # Fill any missing categorical and numerical values before building the feature matrix.
    feature_df = df.copy()

    feature_df["type"] = feature_df["type"].fillna("Unknown")
    feature_df["status"] = feature_df["status"].fillna("Unknown")
    feature_df["classification"] = feature_df["classification"].fillna("Unknown")
    feature_df["risk_class"] = feature_df["risk_class"].fillna("Unknown")
    feature_df["country_event"] = feature_df["country_event"].fillna("Unknown")
    feature_df["country_device"] = feature_df["country_device"].fillna("Unknown")
    feature_df["implanted"] = feature_df["implanted"].fillna("Unknown")
    feature_df["name_manufacturer"] = feature_df["name_manufacturer"].fillna("Unknown")

    feature_df["quantity_in_commerce"] = pd.to_numeric(feature_df["quantity_in_commerce"], errors="coerce")
    feature_df["event_count"] = pd.to_numeric(feature_df["event_count"], errors="coerce")
    feature_df["manufacturer_event_count"] = pd.to_numeric(feature_df["manufacturer_event_count"], errors="coerce")
    feature_df["event_year"] = pd.to_numeric(feature_df["event_year"], errors="coerce")
    feature_df["event_month"] = pd.to_numeric(feature_df["event_month"], errors="coerce")

    for col in FEATURE_COLUMNS:
        if col not in feature_df.columns:
            feature_df[col] = np.nan

    return feature_df[FEATURE_COLUMNS].copy()


def build_pipeline(scale_pos_weight: float):
    """Create the XGBoost pipeline with preprocessing and class imbalance handling."""
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    numerical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
            ("numerical", numerical_pipeline, NUMERICAL_COLUMNS),
        ],
        remainder="drop",
    )

    estimator = XGBClassifier(
        objective="binary:logistic",
        n_estimators=300,
        learning_rate=0.03,
        max_depth=4,
        min_child_weight=2,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
        n_jobs=2,
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", estimator),
    ])


def print_probability_distribution(probabilities, label):
    """Print a compact probability distribution summary without hard-coding any scores."""
    print(f"\n{label} probability stats:")
    print(f"  min      = {np.min(probabilities):.6f}")
    print(f"  max      = {np.max(probabilities):.6f}")
    print(f"  mean     = {np.mean(probabilities):.6f}")
    print(f"  median   = {np.median(probabilities):.6f}")
    print(f"  p05      = {np.percentile(probabilities, 5):.6f}")
    print(f"  p25      = {np.percentile(probabilities, 25):.6f}")
    print(f"  p50      = {np.percentile(probabilities, 50):.6f}")
    print(f"  p75      = {np.percentile(probabilities, 75):.6f}")
    print(f"  p95      = {np.percentile(probabilities, 95):.6f}")

    bins = np.linspace(0, 1, 11)
    hist, edges = np.histogram(probabilities, bins=bins)
    print("  histogram bins (0..1):")
    for i, count in enumerate(hist):
        lo = edges[i]
        hi = edges[i + 1]
        print(f"    [{lo:.2f}, {hi:.2f}) : {count:>6}")


def main():
    print("=== Loading and merging datasets ===")
    merged = load_and_merge_data()

    print("\n=== Building target ===")
    merged["target_raw"] = merged["action_classification"].map(assign_target)
    valid_rows = merged[merged["target_raw"].notna()].copy()
    print(f"Rows before dropping unknown action_classification: {len(merged):,}")
    print(f"Rows after dropping unknown action_classification: {len(valid_rows):,}")

    if valid_rows.empty:
        raise ValueError("No valid training rows remain after filtering action_classification.")

    target_counts = valid_rows["target_raw"].value_counts().sort_index()
    print("Target distribution before training:")
    print(target_counts)

    # Build the exact feature matrix used by the app.
    X = build_feature_frame(valid_rows)
    y = valid_rows["target_raw"].astype(int)

    print("\n=== Train/test split ===")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / pos_count
    print(f"negative_train = {neg_count}")
    print(f"positive_train = {pos_count}")
    print(f"scale_pos_weight = {scale_pos_weight:.4f}")

    print("\n=== Training pipeline ===")
    model = build_pipeline(scale_pos_weight)
    model.fit(X_train, y_train)

    # Calibration is optional but very useful when class imbalance is severe.
    # The final object still keeps the real XGBoost model behavior with calibrated probability output.
    print("\n=== Probability calibration ===")
    calibrator = CalibratedClassifierCV(
        estimator=model,
        method="sigmoid",
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
    )
    calibrator.fit(X_train, y_train)

    y_pred = calibrator.predict(X_test)
    y_proba = calibrator.predict_proba(X_test)[:, 1]

    print_probability_distribution(y_proba, "Test-set")

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    conf = confusion_matrix(y_test, y_pred)
    print("\n=== Evaluation ===")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC: {pr_auc:.4f}")
    print("\nConfusion matrix:")
    print(conf)
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))

    # verify both classes are predicted
    unique_pred = np.unique(y_pred)
    print(f"\nPredicted classes: {unique_pred.tolist()}")
    if len(unique_pred) < 2:
        print("WARNING: The model predicts only one class. This can still happen in extreme imbalance and should be reviewed.")
    else:
        print("Model predicts both classes successfully.")

    # realistic examples from the dataset: low-risk and high-risk rows
    print("\n=== Example predictions from real records ===")
    high_risk_examples = valid_rows[valid_rows["target_raw"] == 1].head(3).copy()
    low_risk_examples = valid_rows[valid_rows["target_raw"] == 0].head(3).copy()

    example_rows = pd.concat([low_risk_examples, high_risk_examples], ignore_index=True)
    example_features = build_feature_frame(example_rows)
    example_probs = calibrator.predict_proba(example_features)[:, 1]
    example_preds = calibrator.predict(example_features)

    example_df = pd.DataFrame({
        "actual_class": example_rows["target_raw"].astype(int).tolist(),
        "predicted_class": example_preds.astype(int).tolist(),
        "risk_probability_pct": (example_probs * 100.0),
        "type": example_features["type"].tolist(),
        "status": example_features["status"].tolist(),
        "classification": example_features["classification"].tolist(),
        "risk_class": example_features["risk_class"].tolist(),
        "manufacturer": example_features["name_manufacturer"].tolist(),
    })

    print(example_df.to_string(index=False, formatters={
        "risk_probability_pct": lambda x: f"{x:.2f}%"
    }))

    # save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibrator, MODEL_PATH)
    print(f"\nSaved calibrated XGBoost pipeline to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
