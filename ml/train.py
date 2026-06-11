import os
import duckdb
import joblib
import pandas as pd
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/nyc_taxi.duckdb")
MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")

FEATURES = [
    "trip_distance",
    "hour_of_day",
    "day_of_week",
    "pu_location_id",
    "do_location_id",
    "passenger_count",
]


def train():
    print("Loading data from staging.stg_trips...")
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = conn.execute("""
        SELECT
            trip_distance,
            EXTRACT(hour FROM pickup_datetime)::INTEGER  AS hour_of_day,
            EXTRACT(dow  FROM pickup_datetime)::INTEGER  AS day_of_week,
            pu_location_id,
            do_location_id,
            COALESCE(passenger_count, 1)                 AS passenger_count,
            fare_amount
        FROM staging.stg_trips
        WHERE fare_amount IS NOT NULL
          AND trip_distance IS NOT NULL
    """).df()
    conn.close()

    print(f"Loaded {len(df):,} rows")

    X = df[FEATURES]
    y = df["fare_amount"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Training on {len(X_train):,} samples, testing on {len(X_test):,}...")

    model = HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.1,
        max_depth=6,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"RMSE: {rmse:.4f}")
    print(f"R2:   {r2:.4f}")

    payload = {
        "model": model,
        "features": FEATURES,
        "trained_at": datetime.utcnow().isoformat(),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "n_train": len(X_train),
    }

    os.makedirs(os.path.dirname(os.path.abspath(MODEL_PATH)), exist_ok=True)
    joblib.dump(payload, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return payload


if __name__ == "__main__":
    train()
