WITH source AS (
    SELECT * FROM raw.taxi_trips_raw
)

SELECT
    pickup_datetime,
    dropoff_datetime,
    pu_location_id,
    do_location_id,
    CAST(trip_distance AS DOUBLE)                                      AS trip_distance,
    CAST(fare_amount AS DOUBLE)                                        AS fare_amount,
    CAST(tip_amount AS DOUBLE)                                         AS tip_amount,
    CAST(total_amount AS DOUBLE)                                       AS total_amount,
    CAST(passenger_count AS INTEGER)                                   AS passenger_count,
    CAST(payment_type AS INTEGER)                                      AS payment_type,
    DATEDIFF('minute', pickup_datetime, dropoff_datetime)              AS trip_duration_minutes,
    ingested_at
FROM source
WHERE fare_amount > 0
  AND trip_distance > 0
  AND pickup_datetime IS NOT NULL
  AND pu_location_id IS NOT NULL
  AND YEAR(pickup_datetime) BETWEEN 2019 AND 2025
