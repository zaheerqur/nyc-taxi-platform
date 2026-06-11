import os
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")

app = FastAPI(title="NYC Taxi Fare Predictor")

_meta = None
_predictions_count = 0
_predictions_total = 0.0


def _load_model():
    global _meta
    if _meta is None:
        _meta = joblib.load(MODEL_PATH)
    return _meta


@app.on_event("startup")
def startup():
    try:
        _load_model()
        print(f"Model loaded - version {_meta['trained_at'][:10]}, R2={_meta['r2']}")
    except Exception as e:
        print(f"Warning: model not loaded at startup - {e}")


class TripFeatures(BaseModel):
    trip_distance: float
    hour_of_day: int
    day_of_week: int
    pu_location_id: int
    do_location_id: int
    passenger_count: int


class FarePrediction(BaseModel):
    predicted_fare: float
    model_version: str


@app.get("/health")
def health():
    try:
        meta = _load_model()
        return {"status": "ok", "model_version": meta["trained_at"][:10]}
    except Exception:
        raise HTTPException(status_code=503, detail="Model not loaded")


@app.post("/predict", response_model=FarePrediction)
def predict(trip: TripFeatures):
    global _predictions_count, _predictions_total
    try:
        meta = _load_model()
    except Exception:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = [
        trip.trip_distance,
        trip.hour_of_day,
        trip.day_of_week,
        trip.pu_location_id,
        trip.do_location_id,
        trip.passenger_count,
    ]
    fare = round(float(meta["model"].predict([features])[0]), 2)

    _predictions_count += 1
    _predictions_total += fare

    return FarePrediction(
        predicted_fare=fare,
        model_version=meta["trained_at"][:10],
    )


@app.get("/metrics")
def metrics():
    avg = round(_predictions_total / _predictions_count, 2) if _predictions_count else 0.0
    return {
        "total_predictions": _predictions_count,
        "avg_predicted_fare": avg,
    }
