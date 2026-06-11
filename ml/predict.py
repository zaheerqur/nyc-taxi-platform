import os
import joblib

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")
_cache = None


def _load():
    global _cache
    if _cache is None:
        _cache = joblib.load(MODEL_PATH)
    return _cache


def predict(features: dict) -> float:
    meta = _load()
    X = [[features[f] for f in meta["features"]]]
    return round(float(meta["model"].predict(X)[0]), 2)


def model_version() -> str:
    return _load()["trained_at"][:10]


def is_loaded() -> bool:
    try:
        _load()
        return True
    except Exception:
        return False
