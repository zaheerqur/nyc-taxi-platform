WITH trips AS (
    SELECT * FROM {{ ref('stg_trips') }}
)

SELECT
    EXTRACT(hour FROM pickup_datetime)      AS hour_of_day,
    EXTRACT(dow FROM pickup_datetime)       AS day_of_week,
    pu_location_id,
    COUNT(*)                                AS trip_count,
    ROUND(AVG(fare_amount), 2)              AS avg_fare
FROM trips
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
