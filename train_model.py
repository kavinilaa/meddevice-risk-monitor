"""Train and save a medical-device risk XGBoost pipeline.

This script:
1) loads the CSV datasets shipped with the project,
2) joins events to devices and devices to manufacturers,
3) builds the 13 model features expected by the FastAPI app,
4) filters to rows with known action_classification values,
5) maps the target using the required Low Risk / High Risk logic,
6) trains an XGBoost pipeline with preprocessing,
7) evaluates the model, and
8) saves the final sklearn pipeline to backend/ml/medical_device_xgboost_13features.pkl.

The saved pipeline is compatible with backend/app/services/model_service.py, which
calls model.predict() and model.predict_proba().
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

# -----------------------------------------------------------------------------
# Project paths
# -----------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
MODEL_PATH = ROOT_DIR / "backend" / "ml" / "medical_device_xgboost_13features.pkl"

# -----------------------------------------------------------------------------
# Model feature specification from the FastAPI service
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Data cleanup helpers
# -----------------------------------------------------------------------------
def clean_text(value):
    """Normalize strings coming from CSVs into clean, comparable values."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_action_classification(value):
    """Map action_classification values to the required binary target.

    Required mapping:
    - Class 1 / Class I / 1 => 0 (Low Risk)
    - Class 2 / Class II / 2 => 0 (Low Risk)
    - Class 3 / Class III / 3 => 1 (High Risk)

    Missing or unknown values are intentionally dropped instead of treated as Low Risk.
    """
    if pd.isna(value):
        return np.nan

    cleaned = str(value).strip()
    if not cleaned:
        return np.nan

    # Remove spaces/punctuation so values like "Class I", "Class-1", or "I" map consistently.
    normalized = re.sub(r"[^A-Z0-9]", "", cleaned.upper())

    if normalized in {"CLASSI", "CLASS1", "I", "1"}:
        return 0
    if normalized in {"CLASSII", "CLASS2", "II", "2"}:
        return 1
    if normalized in {"CLASSIII", "CLASS3", "III", "3"}:
        return 1

    return np.nan


def make_usable_feature_df(df):
    """Convert merged raw data into the exact feature schema expected by the model."""
    # String normalization for categorical fields.
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(clean_text)

    # Normalize boolean-ish fields that may appear as Yes/No or Y/N.
    if "implanted" in df.columns:
        df["implanted"] = df["implanted"].map(lambda x: str(x).strip().upper() if str(x).strip() else "")

    # Standardize some common risk-class variants.
    if "risk_class" in df.columns:
        df["risk_class"] = df["risk_class"].map(lambda x: str(x).strip() if str(x).strip() else "")

    # Fill obvious missing categories with "Unknown" so the one-hot encoder can process them.
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].replace({"": "Unknown"})

    # Numeric columns should be usable numeric values. Coerce invalid values to NaN.
    for col in NUMERICAL_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # We also want these columns to exist in the final schema.
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # Ensure the final order matches the FastAPI feature order exactly.
    df = df[FEATURE_COLUMNS].copy()
    return df


# -----------------------------------------------------------------------------
# Loading and merging datasets
# -----------------------------------------------------------------------------
def load_and_merge_datasets():
    """Load the three raw CSV files and merge them to the training-ready form."""
    devices = pd.read_csv(DATA_DIR / "devices-1681209661.csv", low_memory=False)
    manufacturers = pd.read_csv(DATA_DIR / "manufacturers-1681209657.csv", low_memory=False)

    print(f"Devices rows: {len(devices):,}")
    print(f"Manufacturers rows: {len(manufacturers):,}")

    # Read events in chunks to avoid out-of-memory on large CSV
    print("Reading events CSV in chunks...")
    events_chunks = []
    for chunk in pd.read_csv(DATA_DIR / "events-1681209680.csv", low_memory=False,
                             usecols=["device_id", "type", "status", "country", "action_classification", "date"],
                             chunksize=50000, on_bad_lines="skip"):
        events_chunks.append(chunk)
    events = pd.concat(events_chunks, ignore_index=True)
    print(f"Events rows: {len(events):,}")
    del events_chunks

    # Keep only the columns we need for the merge and feature set.
    devices_subset = devices[[
        "id",
        "manufacturer_id",
        "classification",
        "implantation_status" if "implantation_status" in devices.columns else "implanted",
        "country",
        "name",
        "quantity_in_commerce",
        "risk_class",
    ]].copy()

    # The existing app uses the column "implanted" on the device table;
    # normalise the column name so the feature schema is consistent.
    if "implantation_status" in devices_subset.columns and "implanted" not in devices_subset.columns:
        devices_subset = devices_subset.rename(columns={"implantation_status": "implanted"})

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

    # Merge events -> devices using events.device_id = devices.id
    merged = events[["device_id", "type", "status", "country", "action_classification", "date"]].merge(
        devices_subset,
        on="device_id",
        how="inner",
    )

    # Merge manufacturers using devices.manufacturer_id = manufacturers.id
    merged = merged.merge(
        manufacturers_subset,
        on="manufacturer_id",
        how="left",
    )

    # Derive event_year and event_month from the event date.
    merged["date_parsed"] = pd.to_datetime(merged["date"], errors="coerce")
    merged["event_year"] = merged["date_parsed"].dt.year
    merged["event_month"] = merged["date_parsed"].dt.month

    # Count events per device and per manufacturer to create the required numerical features.
    device_event_counts = merged.groupby("device_id").size().rename("event_count")
    manufacturer_event_counts = merged.groupby("manufacturer_id").size().rename("manufacturer_event_count")

    merged = merged.merge(device_event_counts, on="device_id", how="left")
    merged = merged.merge(manufacturer_event_counts, on="manufacturer_id", how="left")

    # Keep the canonical column names required by the app.
    merged = merged.rename(columns={
        "country_x": "country_event",
        "country_y": "country_device",
    })

    if "country" in merged.columns:
        merged = merged.rename(columns={"country": "country_event"})

    if "device_name" not in merged.columns and "name" in merged.columns:
        merged = merged.rename(columns={"name": "device_name"})

    # Clean up and create a final feature DataFrame.
    merged["country_event"] = merged["country_event"].map(clean_text)
    merged["country_device"] = merged["country_device"].map(clean_text)
    merged["type"] = merged["type"].map(clean_text)
    merged["status"] = merged["status"].map(clean_text)
    merged["classification"] = merged["classification"].map(clean_text)
    merged["risk_class"] = merged["risk_class"].map(clean_text)
    merged["implanted"] = merged["implanted"].map(lambda x: str(x).strip().upper() if str(x).strip() else "")
    merged["name_manufacturer"] = merged["name_manufacturer"].map(clean_text)

    return merged


# -----------------------------------------------------------------------------
# Training pipeline setup
# -----------------------------------------------------------------------------
def build_pipeline(scale_pos_weight):
    """Create the sklearn pipeline required by the application and XGBoost training."""
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_transformer, CATEGORICAL_COLUMNS),
            ("numerical", numerical_transformer, NUMERICAL_COLUMNS),
        ],
        remainder="drop",
    )

    model = XGBClassifier(
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

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    return pipeline


# -----------------------------------------------------------------------------
# Main pipeline execution
# -----------------------------------------------------------------------------
def main():
    """Run full training, evaluation, and serialization."""
    print("\n=== Loading datasets ===")
    merged = load_and_merge_datasets()

    print("\n=== Preparing target label ===")
    merged["target_raw"] = merged["action_classification"].map(normalize_action_classification)
    before_drop = len(merged)
    merged = merged[merged["target_raw"].notna()].copy()
    after_drop = len(merged)
    print(f"Rows before filtering unknown action_classification: {before_drop:,}")
    print(f"Rows after filtering to known action classes: {after_drop:,}")

    if merged.empty:
        raise ValueError("No usable rows remain after filtering action_classification. Check the CSV values.")

    # Build the required 13-feature schema.
    df = merged.copy()
    df["type"] = df["type"].fillna("Unknown")
    df["status"] = df["status"].fillna("Unknown")
    df["classification"] = df["classification"].fillna("Unknown")
    df["risk_class"] = df["risk_class"].fillna("Unknown")
    df["country_event"] = df["country_event"].fillna("Unknown")
    df["country_device"] = df["country_device"].fillna("Unknown")
    df["implanted"] = df["implanted"].fillna("Unknown")
    df["name_manufacturer"] = df["name_manufacturer"].fillna("Unknown")
    df["quantity_in_commerce"] = pd.to_numeric(df["quantity_in_commerce"], errors="coerce")
    df["event_count"] = pd.to_numeric(df["event_count"], errors="coerce")
    df["manufacturer_event_count"] = pd.to_numeric(df["manufacturer_event_count"], errors="coerce")
    df["event_year"] = pd.to_numeric(df["event_year"], errors="coerce")
    df["event_month"] = pd.to_numeric(df["event_month"], errors="coerce")

    # Binary target definition required by the specification.
    df["target"] = df["target_raw"].astype(int)

    # Target distribution before training.
    target_distribution = df["target"].value_counts().sort_index()
    print("\nTarget distribution before training:")
    print(target_distribution)
    print(f"Positive class (High Risk): {int(target_distribution.get(1, 0)):,}")
    print(f"Negative class (Low Risk): {int(target_distribution.get(0, 0)):,}")

    # Ensure the exact required feature order for pipeline predict() compatibility.
    X = df[FEATURE_COLUMNS].copy()
    y = df["target"].astype(int)

    # Train/test split as required.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    negative_count = int((y_train == 0).sum())
    positive_count = int((y_train == 1).sum())
    if positive_count == 0:
        raise ValueError("Positive class is absent in the training split. Cannot train the model.")

    scale_pos_weight = negative_count / positive_count
    print(f"\nScale_pos_weight = negative / positive = {negative_count} / {positive_count} = {scale_pos_weight:.4f}")

    pipeline = build_pipeline(scale_pos_weight)
    print("\n=== Training XGBoost model ===")
    pipeline.fit(X_train, y_train)

    print("\n=== Model evaluation ===")
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    conf_matrix = confusion_matrix(y_test, y_pred)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print("\nConfusion matrix:")
    print(conf_matrix)
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))

    # Probability statistics from predict_proba() directly - no scaling or adjustment.
    prob_stats = {
        "minimum": float(np.min(y_proba)),
        "maximum": float(np.max(y_proba)),
        "mean": float(np.mean(y_proba)),
        "median": float(np.median(y_proba)),
        "95th_percentile": float(np.percentile(y_proba, 95)),
    }
    print("\nProbability statistics from predict_proba():")
    for key, value in prob_stats.items():
        print(f"{key}: {value:.6f}")

    # Verify that the model predicts both classes.
    unique_pred_classes = np.unique(y_pred)
    print(f"\nPredicted classes in test set: {unique_pred_classes.tolist()}")
    if len(unique_pred_classes) < 2:
        print("WARNING: The model predicts only one class. This usually indicates a severe class imbalance or training issue.")
    else:
        print("Model predicts both classes successfully.")

    # Print at least 20 example predictions.
    print("\nSample predictions (first 20):")
    sample_rows = pd.DataFrame({
        "actual_class": y_test.reset_index(drop=True).iloc[:20].astype(int).to_numpy(),
        "predicted_class": y_pred[:20],
        "risk_probability_pct": (y_proba[:20] * 100.0),
    })
    print(sample_rows.to_string(index=False, formatters={
        "risk_probability_pct": lambda x: f"{x:.2f}%"
    }))

    # Save the full sklearn pipeline for compatibility with the app.
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nPipeline saved to: {MODEL_PATH}")

    print("\nTraining complete.")


if __name__ == "__main__":
    main()
