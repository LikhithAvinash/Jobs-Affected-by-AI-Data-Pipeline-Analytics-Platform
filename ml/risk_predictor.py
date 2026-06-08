"""
ML Component: Job Automation Risk Predictor.

Given a job description, predicts:
  - Risk Score (0.0 – 1.0)
  - Risk Category (Low / Medium / High)

Uses TF-IDF features + XGBoost (or Random Forest fallback).
"""

import logging
import os
import pickle
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models_trained")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.pkl")

# ── Keywords associated with automation risk levels ──
# Expanded keyword sets for better coverage across job types

HIGH_RISK_KEYWORDS = [
    # Administrative / clerical
    "data entry", "bookkeeping", "transcription", "filing", "clerical",
    "receptionist", "cashier", "assembly line", "routine", "repetitive",
    "manual processing", "sorting", "scanning", "document processing",
    "order processing", "invoice", "billing", "payroll processing",
    # Support / basic tasks
    "customer service", "call center", "helpdesk", "technical support",
    "troubleshooting", "ticket", "scheduling", "appointment",
    # Basic testing / QA
    "manual testing", "test cases", "regression testing",
    # Operations
    "warehouse", "inventory", "dispatch", "logistics coordinator",
    "monitoring", "alert", "escalation", "sop", "standard operating",
    # Basic reporting
    "generate reports", "report generation", "data collection",
    "spreadsheet", "excel", "documentation", "record keeping",
]

MEDIUM_RISK_KEYWORDS = [
    # Development (partially automatable)
    "develop", "implement", "code", "programming", "software",
    "application", "system", "database", "api", "integration",
    "deploy", "maintain", "debug", "troubleshoot", "configure",
    "testing", "quality assurance", "automation", "scripting",
    # Analysis
    "analyze", "analysis", "metrics", "performance", "optimize",
    "requirements", "specifications", "evaluate", "assess",
    # Standard engineering
    "engineer", "developer", "administrator", "analyst",
]

LOW_RISK_KEYWORDS = [
    # AI/ML (creates AI, less replaceable)
    "machine learning", "deep learning", "artificial intelligence",
    "neural network", "nlp", "computer vision", "reinforcement learning",
    "large language model", "llm", "generative ai", "transformer",
    "model training", "feature engineering", "ml pipeline",
    # Strategic / leadership
    "strategy", "leadership", "lead", "director", "manager",
    "stakeholder", "executive", "vision", "roadmap", "mentor",
    "cross-functional", "decision making", "principal", "senior",
    # Creative / complex
    "creative", "design thinking", "innovation", "research",
    "architect", "architecture", "complex problem", "novel",
    "negotiation", "relationship", "collaboration", "influence",
    # Healthcare
    "patient care", "clinical", "diagnosis", "treatment",
    "nurse", "physician", "therapist", "counselor",
]


def _generate_synthetic_labels(descriptions: List[str]) -> List[int]:
    """
    Generate synthetic automation risk labels based on keyword heuristics.
    0 = Low, 1 = Medium, 2 = High

    Uses a weighted scoring system across all three categories for
    more nuanced classification.
    """
    labels = []
    for desc in descriptions:
        desc_lower = desc.lower() if desc else ""

        high_score = sum(2 for kw in HIGH_RISK_KEYWORDS if kw in desc_lower)
        medium_score = sum(1 for kw in MEDIUM_RISK_KEYWORDS if kw in desc_lower)
        low_score = sum(2 for kw in LOW_RISK_KEYWORDS if kw in desc_lower)

        # Determine category based on weighted scores
        if high_score > low_score and high_score > medium_score:
            labels.append(2)  # High risk
        elif low_score > high_score and low_score >= medium_score:
            labels.append(0)  # Low risk
        else:
            labels.append(1)  # Medium risk

    return labels


def train_model(descriptions: List[str], labels: List[int] = None) -> Dict:
    """
    Train the automation risk prediction model.

    Args:
        descriptions: List of job description strings
        labels: Optional pre-existing labels. If None, generates synthetic labels.

    Returns:
        Dict with training metrics.
    """
    if labels is None:
        labels = _generate_synthetic_labels(descriptions)

    # Check class distribution
    from collections import Counter
    dist = Counter(labels)
    logger.info("Label distribution: %s", dict(dist))

    # Ensure all classes have at least 2 members for stratified split
    min_count = min(dist.values())
    use_stratify = min_count >= 2

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
    )
    X = vectorizer.fit_transform(descriptions)
    y = np.array(labels)

    # Train/test split (with or without stratification)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if use_stratify else None,
    )

    # Model selection
    if HAS_XGBOOST:
        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective="multi:softprob",
            num_class=3,
            random_state=42,
            eval_metric="mlogloss",
        )
    else:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
        )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    logger.info("Model accuracy: %.3f", report["accuracy"])

    # Save model and vectorizer
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    logger.info("Model saved to %s", MODEL_PATH)
    return report


def predict_risk(description: str) -> Tuple[float, str]:
    """
    Predict automation risk for a single job description.

    Returns:
        (risk_score, risk_category) where score is 0.0-1.0
        and category is 'Low', 'Medium', or 'High'.
    """
    CATEGORY_MAP = {0: "Low", 1: "Medium", 2: "High"}

    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    X = vectorizer.transform([description])
    proba = model.predict_proba(X)[0]

    # Ensure we have probabilities for all 3 classes
    if len(proba) < 3:
        # Model may not have seen all classes; pad with zeros
        full_proba = np.zeros(3)
        for i, cls in enumerate(model.classes_):
            full_proba[cls] = proba[i]
        proba = full_proba

    pred_class = int(np.argmax(proba))

    # Risk score: weighted combination favouring the "High" probability
    risk_score = round(float(proba[2] * 1.0 + proba[1] * 0.5 + proba[0] * 0.0), 4)
    category = CATEGORY_MAP[pred_class]

    return risk_score, category


def batch_predict(descriptions: List[str]) -> pd.DataFrame:
    """
    Predict risk for a batch of descriptions.
    Returns a DataFrame with columns: description, risk_score, risk_category.
    """
    results = []
    for desc in descriptions:
        score, cat = predict_risk(desc)
        results.append({
            "description": desc[:200],
            "risk_score": score,
            "risk_category": cat,
        })
    return pd.DataFrame(results)
