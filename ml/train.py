# File: ml/train.py

import os
import joblib
import pandas as pd
from pathlib import Path
from feature_store import get_features

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

def run_training():
    # 1. Ingest Data
    print("📥 Fetching ML features from BigQuery via Feature Store...")
    df = get_features()

    if df.empty:
        print("❌ Error: No data found. Check your dbt run.")
        return

    # 2. Advanced Feature Engineering (Adding multi-day lag for better signals)
    print("📈 Engineering extra financial features...")
    df = df.sort_values('price_date')
    df['return_lag_1'] = df['daily_return'].shift(1)
    df['return_lag_2'] = df['daily_return'].shift(2)
    
    # Clean Data
    df = df.dropna()
    df = df.drop_duplicates()

    # 3. Prepare Features and Target
    X = df.drop(columns=['target_direction', 'price_date'])
    y = df['target_direction']

    # FIX: Explicitly extract selected feature names for serialization
    selected_features = X.columns.tolist()

    num_col = X.select_dtypes(include='number').columns.tolist()
    cat_col = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Time-series split
    print("✂️ Splitting data chronologically...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Calculate scale_pos_weight to handle class imbalance (Low recall fix)
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0

    # 4. Build Preprocessing Pipelines
    print("🏗️ Building Preprocessing ColumnTransformer...")
    num_pipeline = Pipeline(steps=[
        ('impute', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_pipeline = Pipeline(steps=[
        ('impute', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ('num', num_pipeline, num_col),
        ('cat', cat_pipeline, cat_col)
    ])

    # 5. Define XGBoost with balancing parameter
    print("🧠 Initializing Tuned XGBoost Classifier...")
    model = XGBClassifier(
        n_estimators=150, 
        max_depth=4, 
        learning_rate=0.05, 
        subsample=0.8,
        scale_pos_weight=scale_weight, # Fixes low recall on minority class
        random_state=42
    )

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])

    # 6. Train and Evaluate
    print("⏳ Training model pipeline...")
    model_pipeline.fit(X_train, y_train)
    predictions = model_pipeline.predict(X_test)

    print("\n📊 Optimized Evaluation Metrics on Holdout Test Set:")
    print("--------------------------------------------------")
    print(classification_report(y_test, predictions, zero_division=0))
    print("Confusion Matrix:\n", confusion_matrix(y_test, predictions))
    print("--------------------------------------------------")

    # 7. Save Artifacts
    BASE_DIR = Path(__file__).resolve().parent
    ARTIFACTS_DIR = BASE_DIR / "artifacts"
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model_pipeline, ARTIFACTS_DIR / "trading_model.pkl")
    joblib.dump(selected_features, ARTIFACTS_DIR / "model_features.pkl")
    
    print("🚀 Done! Optimized model saved to ml/artifacts/")

if __name__ == "__main__":
    run_training()