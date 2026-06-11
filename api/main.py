import os
import duckdb
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

MODEL_PATH  = os.getenv("MODEL_PATH",  "ml/model.pkl")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/nyc_taxi.duckdb")

app = FastAPI(title="NYC Taxi Fare Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_meta = None
_predictions_count = 0
_predictions_total = 0.0


def _load_model():
    global _meta
    if _meta is None:
        _meta = joblib.load(MODEL_PATH)
    return _meta


def _db():
    return duckdb.connect(DUCKDB_PATH, read_only=True)


@app.on_event("startup")
def startup():
    try:
        _load_model()
        print(f"Model loaded - version {_meta['trained_at'][:10]}, R2={_meta['r2']}")
    except Exception as e:
        print(f"Warning: model not loaded at startup - {e}")


# ── Pydantic models ───────────────────────────────────────────────────────────

class TripFeatures(BaseModel):
    trip_distance:  float
    hour_of_day:    int
    day_of_week:    int
    pu_location_id: int
    do_location_id: int
    passenger_count: int


class FarePrediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    predicted_fare: float
    model_version:  str


# ── Prediction endpoints ──────────────────────────────────────────────────────

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
        trip.trip_distance, trip.hour_of_day, trip.day_of_week,
        trip.pu_location_id, trip.do_location_id, trip.passenger_count,
    ]
    fare = round(float(meta["model"].predict([features])[0]), 2)
    _predictions_count += 1
    _predictions_total += fare
    return FarePrediction(predicted_fare=fare, model_version=meta["trained_at"][:10])


@app.get("/metrics")
def metrics():
    avg = round(_predictions_total / _predictions_count, 2) if _predictions_count else 0.0
    return {"total_predictions": _predictions_count, "avg_predicted_fare": avg}


# ── Dashboard data endpoints ──────────────────────────────────────────────────

@app.get("/stats/trip-volume")
def trip_volume():
    conn = _db()
    rows = conn.execute("""
        SELECT trip_date::VARCHAR AS date, SUM(total_trips)::INTEGER AS trips
        FROM mart.fare_summary
        GROUP BY trip_date ORDER BY trip_date
    """).fetchall()
    conn.close()
    return [{"date": r[0], "trips": r[1]} for r in rows]


@app.get("/stats/revenue")
def revenue():
    conn = _db()
    rows = conn.execute("""
        SELECT COALESCE(pickup_borough, 'Unknown') AS borough,
               ROUND(SUM(total_revenue), 2)        AS revenue
        FROM mart.fare_summary
        GROUP BY pickup_borough
        ORDER BY revenue DESC
    """).fetchall()
    conn.close()
    return [{"borough": r[0], "revenue": float(r[1])} for r in rows]


@app.get("/stats/demand")
def demand():
    conn = _db()
    rows = conn.execute("""
        SELECT hour_of_day::INTEGER  AS hour,
               day_of_week::INTEGER  AS day,
               SUM(trip_count)::INTEGER AS trips
        FROM mart.hourly_demand
        GROUP BY hour_of_day, day_of_week
        ORDER BY day, hour
    """).fetchall()
    conn.close()
    return [{"hour": r[0], "day": r[1], "trips": r[2]} for r in rows]
