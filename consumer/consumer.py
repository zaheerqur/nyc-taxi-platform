import os
import sys
import json
import signal
import logging
import duckdb
import pandas as pd
from datetime import datetime, timezone
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/nyc_taxi.duckdb")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))
TOPIC = "taxi-trips"
CONSUMER_GROUP = "taxi-consumer-group"

CREATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.taxi_trips_raw (
    pickup_datetime     TIMESTAMP,
    dropoff_datetime    TIMESTAMP,
    pu_location_id      INTEGER,
    do_location_id      INTEGER,
    trip_distance       DOUBLE,
    fare_amount         DOUBLE,
    tip_amount          DOUBLE,
    total_amount        DOUBLE,
    passenger_count     INTEGER,
    payment_type        INTEGER,
    ingested_at         TIMESTAMP
);
"""

running = True


def shutdown(sig, frame):
    global running
    log.info("Shutdown signal received — draining current batch...")
    running = False


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def insert_batch(conn, batch):
    rows = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for msg in batch:
        try:
            data = json.loads(msg)
            rows.append({
                "pickup_datetime": data.get("pickup_datetime"),
                "dropoff_datetime": data.get("dropoff_datetime"),
                "pu_location_id": data.get("pu_location_id"),
                "do_location_id": data.get("do_location_id"),
                "trip_distance": data.get("trip_distance"),
                "fare_amount": data.get("fare_amount"),
                "tip_amount": data.get("tip_amount"),
                "total_amount": data.get("total_amount"),
                "passenger_count": data.get("passenger_count"),
                "payment_type": data.get("payment_type"),
                "ingested_at": now,
            })
        except (json.JSONDecodeError, KeyError) as e:
            log.warning("Skipping malformed message: %s", e)

    if not rows:
        return 0

    df = pd.DataFrame(rows)
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

    start = datetime.now()
    conn.execute("INSERT INTO raw.taxi_trips_raw SELECT * FROM df")
    elapsed = (datetime.now() - start).total_seconds()
    log.info("Inserted %d rows in %.3fs", len(rows), elapsed)
    return len(rows)


def main():
    conn = duckdb.connect(DUCKDB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    log.info("DuckDB ready at %s", DUCKDB_PATH)

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([TOPIC])
    log.info("Subscribed to topic: %s", TOPIC)

    batch = []
    total_inserted = 0

    try:
        while running:
            msg = consumer.poll(timeout=5.0)

            if msg is None:
                if batch:
                    total_inserted += insert_batch(conn, batch)
                    consumer.commit()
                    batch = []
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                log.error("Kafka error: %s", msg.error())
                continue

            batch.append(msg.value().decode("utf-8"))

            if len(batch) >= BATCH_SIZE:
                total_inserted += insert_batch(conn, batch)
                consumer.commit()
                batch = []

    finally:
        if batch:
            total_inserted += insert_batch(conn, batch)
            consumer.commit()
        consumer.close()
        conn.close()
        log.info("Consumer shut down cleanly. Total rows inserted: %d", total_inserted)


if __name__ == "__main__":
    main()
