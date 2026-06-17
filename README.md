# NYC Taxi Analytics Platform

A data engineering portfolio project built on 9.5 million NYC Yellow Taxi trips (Jan-Mar 2024). Demonstrates event-driven ingestion, a layered warehouse, schema-tested transformations, scheduled orchestration, and an ML-powered prediction API. The entire stack runs locally with a single Docker Compose command.

[![dbt CI](https://github.com/zaheerqur/nyc-taxi-platform/actions/workflows/dbt_ci.yml/badge.svg)](https://github.com/zaheerqur/nyc-taxi-platform/actions/workflows/dbt_ci.yml)

**Live dashboard:** https://nyc-taxi-dashboard.netlify.app
**API docs:** https://nyc-taxi-api-z25x.onrender.com/docs

---

## What it does

Trip records are streamed record-by-record from NYC TLC Parquet files into a Kafka topic, consumed in batches into DuckDB, and transformed through dbt staging and mart layers. Apache Airflow orchestrates the pipeline on a 30-minute schedule and triggers model retraining when enough new data has accumulated. A FastAPI backend serves aggregated stats and fare predictions to a React dashboard.

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
                                   [FastAPI]  (port 8000)
                                          |
                                          v
                               [React Dashboard]  (port 3000)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Message broker | Apache Kafka (KRaft mode) |
| Warehouse | DuckDB |
| Transformations | dbt Core + dbt-duckdb |
| Orchestration | Apache Airflow |
| ML | scikit-learn HistGradientBoostingRegressor |
| API | FastAPI + Uvicorn |
| Dashboard | React 18 + Recharts + Vite |
| Infrastructure | Docker Compose |
| CI | GitHub Actions |

---

## ML Model

Trained on `staging.stg_trips` using `HistGradientBoostingRegressor` with features: trip distance, hour of day, day of week, pickup/dropoff location, and passenger count.

| Metric | Value |
|---|---|
| R² | 0.91 |
| RMSE | $6.54 |

Airflow retrains automatically when the row count grows by 50,000+ since the last run.

---

## Airflow Pipeline

```
check_kafka_lag -> run_dbt_staging -> run_dbt_marts -> run_dbt_tests -> retrain_model -> notify_success
```

9 dbt tests run on every pipeline execution covering nullability, referential integrity, accepted values, and a custom positive-fares assertion.

---

## Running Locally

**Prerequisites:** Docker Desktop, Python 3.11+

```bash
git clone https://github.com/zaheerqur/nyc-taxi-platform.git
cd nyc-taxi-platform
```

Download [Jan-Mar 2024 Yellow Taxi Parquet files](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) into `data/`, then:

```bash
docker compose up -d
python producer/producer.py
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Airflow | http://localhost:8080 |

---

## Production Scaling Notes

This runs on a single machine for portfolio purposes. In production:

- **Kafka** would be a managed cluster (Confluent Cloud, MSK) with replication factor 3
- **DuckDB** would give way to a cloud warehouse (Snowflake, BigQuery) or MotherDuck
- **Airflow** would use CeleryExecutor or KubernetesExecutor with a Postgres metadata DB
- **ML** would be versioned in MLflow and served behind a dedicated inference service
- **API** would sit behind a load balancer with horizontal scaling

---

## Data Source

NYC Taxi and Limousine Commission (TLC) Trip Record Data - Yellow Taxi, January-March 2024.
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
