# File: api/app.py

import joblib
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Cross-platform path resolution ──────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
MODEL_PATH    = BASE_DIR / "ml" / "artifacts" / "trading_model.pkl"
FEATURES_PATH = BASE_DIR / "ml" / "artifacts" / "model_features.pkl"

# ── Load artifacts at startup ────────────────────────────────────────────────
model_pipeline    = None
expected_features = None

try:
    if MODEL_PATH.exists() and FEATURES_PATH.exists():
        model_pipeline = joblib.load(MODEL_PATH)
        raw_features   = joblib.load(FEATURES_PATH)
        
        # Convert numpy/pandas array to plain Python list safely
        if hasattr(raw_features, "tolist"):
            expected_features = raw_features.tolist()
        else:
            expected_features = list(raw_features)

        print(f"✅ Model loaded from  : {MODEL_PATH}")
        print(f"✅ Features loaded    : {expected_features}")
    else:
        print("⚠️ Artifact files missing in /app/ml/artifacts/")
except Exception as e:
    print(f"❌ Error loading model artifacts: {e}")


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health_check():
    """Health-check endpoint — used by Streamlit & Docker Healthcheck."""
    is_ready = (model_pipeline is not None) and (expected_features is not None)
    
    # ALWAYS return 200 OK so Docker healthcheck passes
    return jsonify({
        "status": "API is running",
        "model_loaded": is_ready,
        "expected_features": expected_features if expected_features is not None else [],
        "artifacts": {
            "model_path": str(MODEL_PATH),
            "features_path": str(FEATURES_PATH),
        }
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    if model_pipeline is None or expected_features is None:
        return jsonify({
            "error": "Model pipeline or feature list not loaded on server.",
            "hint": "Run ml/train.py to generate artifacts, then restart the API."
        }), 500

    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({
                "error": "No JSON payload provided or invalid Content-Type.",
                "hint": "Send a JSON body with Content-Type: application/json"
            }), 400

        # Convert dict → DataFrame and align features
        df = pd.DataFrame([data])
        df = df.reindex(columns=expected_features, fill_value=0)

        prediction    = int(model_pipeline.predict(df)[0])
        probabilities = model_pipeline.predict_proba(df)[0].tolist()
        confidence    = probabilities[1] if prediction == 1 else probabilities[0]

        return jsonify({
            "prediction": prediction,
            "signal":     "BUY" if prediction == 1 else "SELL",
            "confidence_score": round(float(confidence), 4),
            "probabilities": {
                "sell_prob": round(float(probabilities[0]), 4),
                "buy_prob":  round(float(probabilities[1]), 4),
            }
        }), 200

    except ValueError as e:
        return jsonify({"error": f"Data validation error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Internal prediction error: {str(e)}"}), 500


@app.route("/features", methods=["GET"])
def get_features():
    return jsonify({
        "expected_features": expected_features if expected_features is not None else [],
        "feature_count": len(expected_features) if expected_features is not None else 0
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)