# NYC Real-Time Taxi Analytics Platform

A production-grade data engineering portfolio project. Real-time trip data flows from Apache Kafka through a DuckDB warehouse, dbt transformations, and a scikit-learn ML model, surfaced via a FastAPI backend and React dashboard. The entire stack runs locally with a single Docker Compose command.

[![dbt CI](https://github.com/zaheerqur/nyc-taxi-platform/actions/workflows/dbt_ci.yml/badge.svg)](https://github.com/zaheerqur/nyc-taxi-platform/actions/workflows/dbt_ci.yml)

---

## Architecture

```
NYC TLC Parquet Data
        |
        v
[Kafka Producer] ──────────────────────────────────────────────┐
(Python, host)                                                  |
                                                                v
                                          Kafka Topic: taxi-trips
                                          (confluentinc/cp-kafka:7.6.0)
                                                                |
                                                                v
                                                    [Kafka Consumer]
                                                    (Python, Docker)
                                                                |
                                                                v
                                              DuckDB  --  raw.taxi_trips_raw
                                                                |
                                                                v
                                               [dbt Core + dbt-duckdb]
                                               staging.stg_trips
                                               mart.fare_summary
                                               mart.hourly_demand
                                                                |
                                          ┌─────────────────────┴─────────────────────┐
                                          v                                           v
                                [ML Training]                              [Apache Airflow]
                                HistGradientBoosting                       (orchestrates dbt
                                R2=0.91, RMSE=$6.54                          + retraining)
                                          |
                                          v
                                   ml/model.pkl
                                          |
                                          v
                                   [FastAPI]  (port 8000)
                                   POST /predict
                                   GET  /stats/*
                                          |
                                          v
                               [React Dashboard]  (port 3000)
                               Trip Volume  |  Revenue by Borough
                               Demand Heatmap  |  Fare Predictor
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Message broker | Apache Kafka (KRaft mode) | 7.6.0 |
| Warehouse | DuckDB | 0.10.2 |
| Transformations | dbt Core + dbt-duckdb | 1.7.x |
| Orchestration | Apache Airflow | 2.9.3 |
| ML | scikit-learn HistGradientBoostingRegressor | 1.4.2 |
| API | FastAPI + Uvicorn | 0.111.0 |
| Dashboard | React 18 + Recharts + Vite | 18 / 2.12 / 5 |
| Containerisation | Docker Compose | v2 |
| CI | GitHub Actions | - |
| Data | NYC TLC Yellow Taxi (Jan-Mar 2024) | - |

---

## Quick Start

### Prerequisites

- Docker Desktop (WSL 2 backend on Windows)
- Python 3.11+ (for the producer, runs on host)

### 1. Clone

```bash
git clone https://github.com/zaheerqur/nyc-taxi-platform.git
cd nyc-taxi-platform
```

### 2. Download NYC TLC data

Download the [2024 Yellow Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) (January, February, March Parquet files) and place them in `data/`.

### 3. Start the stack

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| FastAPI docs | http://localhost:8000/docs |
| Airflow UI | http://localhost:8080 |

Airflow credentials: `admin` / `yUF3gyeK94XcKkdg`

### 4. Stream data

```bash
pip install -r producer/requirements.txt
python producer/producer.py
```

The producer reads Parquet files and publishes to the `taxi-trips` Kafka topic. The consumer (inside Docker) batches 500 records per insert into DuckDB.

### 5. Trigger the pipeline

Airflow runs on a 30-minute schedule. To run immediately:

```bash
docker exec airflow airflow dags unpause nyc_taxi_pipeline
docker exec airflow airflow dags trigger nyc_taxi_pipeline
```

---

## Project Structure

```
nyc-taxi-platform/
├── producer/           # Kafka producer - reads Parquet, publishes trips
├── consumer/           # Kafka consumer - batched DuckDB inserts
├── dbt_project/        # dbt models, tests, seeds, macros
│   ├── models/
│   │   ├── staging/    # stg_trips - filtering + feature engineering
│   │   └── marts/      # fare_summary, hourly_demand
│   ├── seeds/          # taxi_zone_lookup.csv (265 NYC zones)
│   ├── tests/          # custom SQL tests
│   └── macros/         # generate_schema_name override
├── ml/
│   ├── train.py        # HistGradientBoostingRegressor training
│   └── predict.py      # lazy-loading inference helper
├── api/                # FastAPI - /predict + /stats/* endpoints
├── dashboard/          # React + Recharts - dark theme analytics UI
├── airflow/
│   └── dags/           # pipeline_dag.py - 6-task orchestration DAG
├── data/               # DuckDB warehouse + Parquet files (gitignored)
└── docker-compose.yml  # Full stack orchestration
```

---

## ML Model

Trained on `staging.stg_trips` using a `HistGradientBoostingRegressor`.

**Features:** `trip_distance`, `hour_of_day`, `day_of_week`, `pu_location_id`, `do_location_id`, `passenger_count`

**Results (80/20 split on 80,197 trips):**

| Metric | Value |
|---|---|
| R2 | 0.91 |
| RMSE | $6.54 |

Airflow retrains automatically when the row count grows by 50,000+ since the last run.

---

## dbt Tests

```bash
dbt test --project-dir dbt_project --profiles-dir dbt_project
```

9 tests across staging and mart models:

- `not_null` on fare_amount, trip_distance, pickup_datetime
- `accepted_values` on payment_type (1-6)
- `relationships` - pu_location_id must exist in taxi_zone_lookup
- `assert_positive_fares` - custom SQL test, zero rows allowed

---

## Airflow DAG

`nyc_taxi_pipeline` runs every 30 minutes:

```
check_kafka_lag -> run_dbt_staging -> run_dbt_marts -> run_dbt_tests -> retrain_model -> notify_success
```

---

## API Reference

```
POST /predict              Predict fare for a trip
GET  /health               Service health + model status
GET  /metrics              Model metadata (R2, RMSE, training date)
GET  /stats/trip-volume    Daily trip counts
GET  /stats/revenue        Revenue by borough
GET  /stats/demand         Hour x day-of-week demand heatmap
```

Example:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "trip_distance": 3.5,
    "hour_of_day": 14,
    "day_of_week": 2,
    "pu_location_id": 161,
    "do_location_id": 236,
    "passenger_count": 1
  }'
```

---

## CI

GitHub Actions runs on every push and PR to `main`:

1. Creates a minimal test DuckDB with seed data
2. `dbt compile` - validates all model SQL
3. `dbt run --select staging` - materialises staging views
4. `dbt test --select staging` - runs all schema tests
5. `flake8` - lints Python across producer, consumer, api, ml

---

## Production Scaling Notes

This project runs on a single machine for portfolio purposes. In production:

- **Kafka** would be a managed cluster (Confluent Cloud, MSK) with replication factor 3
- **DuckDB** would give way to a distributed warehouse (BigQuery, Snowflake) or MotherDuck
- **Airflow** would use CeleryExecutor or KubernetesExecutor with a Postgres metadata DB
- **ML** would be versioned in MLflow and served behind a dedicated inference service
- **API** would sit behind a load balancer with horizontal scaling and connection pooling
- **Dashboard** would be a static site on a CDN with server-side caching for expensive queries

The patterns here - event-driven ingestion, layered warehouse (raw/staging/mart), schema-tested transformations, scheduled retraining, real-time API - translate directly to the production stack.

---

## Data Source

NYC Taxi and Limousine Commission (TLC) Trip Record Data - Yellow Taxi, January-March 2024.
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
