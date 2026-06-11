from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

KAFKA_BOOTSTRAP = "kafka:9092"
CONSUMER_GROUP = "taxi-consumer-group"
TOPIC = "taxi-trips"
DUCKDB_PATH = "/opt/airflow/data/nyc_taxi.duckdb"
DBT_FLAGS = "--project-dir /opt/airflow/dbt_project --profiles-dir /opt/airflow/dbt_project"
RETRAIN_THRESHOLD = 50_000

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def _check_kafka_lag(**context):
    from confluent_kafka import Consumer, TopicPartition

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "enable.auto.commit": False,
    })
    try:
        meta = consumer.list_topics(TOPIC, timeout=10)
        partitions = [TopicPartition(TOPIC, pid) for pid in meta.topics[TOPIC].partitions]
        total_lag = 0
        for tp in partitions:
            low, high = consumer.get_watermark_offsets(tp, timeout=10)
            committed = consumer.committed([tp], timeout=10)[0]
            consumed = committed.offset if committed.offset >= 0 else 0
            total_lag += max(0, high - consumed)
        print(f"Consumer group '{CONSUMER_GROUP}' lag: {total_lag:,} messages")
        if total_lag > 10_000:
            raise ValueError(f"Lag {total_lag:,} exceeds threshold of 10,000 — pipeline paused")
        context["ti"].xcom_push(key="kafka_lag", value=total_lag)
    finally:
        consumer.close()


def _maybe_retrain(**context):
    import duckdb
    import subprocess
    import sys

    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    current_count = conn.execute("SELECT COUNT(*) FROM raw.taxi_trips_raw").fetchone()[0]
    conn.close()

    ti = context["ti"]
    last_count = ti.xcom_pull(
        dag_id="nyc_taxi_pipeline",
        task_ids="retrain_model",
        key="row_count",
        include_prior_dates=True,
    ) or 0

    growth = current_count - int(last_count)
    ti.xcom_push(key="row_count", value=current_count)
    print(f"Row count: {current_count:,} (grew by {growth:,} since last run)")

    if growth >= RETRAIN_THRESHOLD:
        print(f"Growth {growth:,} >= threshold {RETRAIN_THRESHOLD:,} — retraining model")
        result = subprocess.run(
            [sys.executable, "/opt/airflow/ml/train.py"],
            capture_output=True, text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(f"Model training failed:\n{result.stderr}")
    else:
        print(f"Growth {growth:,} < threshold {RETRAIN_THRESHOLD:,} — skipping retrain")


def _notify_success(**context):
    import duckdb

    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    raw_count = conn.execute("SELECT COUNT(*) FROM raw.taxi_trips_raw").fetchone()[0]
    staging_count = conn.execute("SELECT COUNT(*) FROM staging.stg_trips").fetchone()[0]
    fare_days = conn.execute("SELECT COUNT(DISTINCT trip_date) FROM mart.fare_summary").fetchone()[0]
    conn.close()

    lag = context["ti"].xcom_pull(task_ids="check_kafka_lag", key="kafka_lag") or "n/a"
    print(f"Pipeline completed at {datetime.utcnow().isoformat()}")
    print(f"  Raw rows:     {raw_count:,}")
    print(f"  Staging rows: {staging_count:,}")
    print(f"  Fare days:    {fare_days}")
    print(f"  Kafka lag:    {lag}")
    print("  Production: wire up Slack/PagerDuty here")


with DAG(
    dag_id="nyc_taxi_pipeline",
    description="Kafka lag check -> dbt staging -> dbt marts -> dbt tests -> optional model retrain",
    schedule_interval="*/30 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["nyc-taxi", "pipeline"],
) as dag:

    check_kafka_lag = PythonOperator(
        task_id="check_kafka_lag",
        python_callable=_check_kafka_lag,
    )

    run_dbt_staging = BashOperator(
        task_id="run_dbt_staging",
        bash_command=f"dbt run --select staging {DBT_FLAGS}",
    )

    run_dbt_marts = BashOperator(
        task_id="run_dbt_marts",
        bash_command=f"dbt run --select marts {DBT_FLAGS}",
    )

    run_dbt_tests = BashOperator(
        task_id="run_dbt_tests",
        bash_command=f"dbt test {DBT_FLAGS}",
    )

    retrain_model = PythonOperator(
        task_id="retrain_model",
        python_callable=_maybe_retrain,
    )

    notify_success = PythonOperator(
        task_id="notify_success",
        python_callable=_notify_success,
    )

    check_kafka_lag >> run_dbt_staging >> run_dbt_marts >> run_dbt_tests >> retrain_model >> notify_success
