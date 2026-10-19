from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).resolve().parent / "models" / "ticket_classifier.joblib"

def suggest_category(description):
    if not MODEL_PATH.exists():
        return {"category": None, "confidence": None,
                "message": "Classifier not trained yet. Run: python scripts/train_classifier.py"}
    model = joblib.load(MODEL_PATH)
    probs = model.predict_proba([description or ""])
    idx = probs[0].argmax()
    return {"category": str(model.classes_[idx]), "confidence": round(float(probs[0][idx]), 4),
            "message": "Suggestion only — agent review is required."}
