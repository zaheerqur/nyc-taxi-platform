import os
import sys
import time
import json
import glob
import logging
import signal
import pandas as pd
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
PRODUCER_DELAY_MS = int(os.getenv("PRODUCER_DELAY_MS", 10)) / 1000
TOPIC = "taxi-trips"
DATA_DIR = os.getenv("DATA_DIR", "data")

COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "passenger_count",
    "payment_type",
]


def delivery_report(err, msg):
    if err:
        log.error("Delivery failed for message %s: %s", msg.key(), err)


def serialize_row(row):
    return json.dumps({
        "pickup_datetime": str(row["tpep_pickup_datetime"]),
        "dropoff_datetime": str(row["tpep_dropoff_datetime"]),
        "pu_location_id": int(row["PULocationID"]) if pd.notna(row["PULocationID"]) else None,
        "do_location_id": int(row["DOLocationID"]) if pd.notna(row["DOLocationID"]) else None,
        "trip_distance": float(row["trip_distance"]) if pd.notna(row["trip_distance"]) else None,
        "fare_amount": float(row["fare_amount"]) if pd.notna(row["fare_amount"]) else None,
        "tip_amount": float(row["tip_amount"]) if pd.notna(row["tip_amount"]) else None,
        "total_amount": float(row["total_amount"]) if pd.notna(row["total_amount"]) else None,
        "passenger_count": int(row["passenger_count"]) if pd.notna(row["passenger_count"]) else None,
        "payment_type": int(row["payment_type"]) if pd.notna(row["payment_type"]) else None,
    })


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

    def shutdown(sig, frame):
        log.info("Shutting down — flushing remaining messages...")
        producer.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    parquet_files = sorted(glob.glob(f"{DATA_DIR}/yellow_tripdata_*.parquet"))

    if not parquet_files:
        log.error("No parquet files found in %s", DATA_DIR)
        return

    log.info("Found %d parquet file(s): %s", len(parquet_files), parquet_files)
    total_published = 0

    for filepath in parquet_files:
        log.info("Loading %s", filepath)
        df = pd.read_parquet(filepath, columns=COLUMNS)
        log.info("Loaded %d rows from %s", len(df), filepath)

        for i, (_, row) in enumerate(df.iterrows()):
            message = serialize_row(row)
            key = str(row["PULocationID"]) if pd.notna(row["PULocationID"]) else "0"

            producer.produce(
                topic=TOPIC,
                key=key,
                value=message,
                on_delivery=delivery_report,
            )
            producer.poll(0)

            total_published += 1
            if total_published % 1000 == 0:
                log.info("Published %d messages total", total_published)

            time.sleep(PRODUCER_DELAY_MS)

        producer.flush()
        log.info("Finished file %s", filepath)

    log.info("Done. Total messages published: %d", total_published)


if __name__ == "__main__":
    main()
