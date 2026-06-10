# NYC Real-Time Taxi Analytics Platform

> WIP — actively being built

Real-time data pipeline ingesting NYC TLC taxi trip data through Kafka, transforming with dbt, loading into DuckDB, serving ML-based fare predictions via FastAPI, and visualizing on a React dashboard.

The full stack runs locally with a single command:

```bash
docker-compose up --build
```

## Stack

| Tool | Purpose |
|---|---|
| Apache Kafka | Event streaming backbone |
| Python | Producer, consumer, feature engineering |
| DuckDB | Analytical warehouse layer |
| dbt Core | SQL transformations + testing |
| Apache Airflow | Pipeline orchestration |
| scikit-learn | Fare prediction model |
| FastAPI | ML prediction API |
| React + Recharts | Dashboard |
| GitHub Actions | CI/CD |
| Docker Compose | Local stack orchestration |

## Architecture

```
NYC TLC Parquet files
        |
        v
[Python Producer] ──> [Kafka: taxi-trips] ──> [Python Consumer]
                                                       |
                                                       v
                                           [DuckDB: raw_taxi_trips]
                                                       |
                                                       v
                                               [dbt transforms]
                                                       |
                                    ┌──────────────────┼─────────────────┐
                                    v                  v                 v
                        stg_trips          fare_summary        hourly_demand
                                                       |
                                                       v
                                           [FastAPI /predict]
                                                       |
                                                       v
                                           [React Dashboard]
```
