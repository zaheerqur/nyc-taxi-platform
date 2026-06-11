WITH trips AS (
    SELECT * FROM {{ ref('stg_trips') }}
),

zones AS (
    SELECT * FROM {{ ref('taxi_zone_lookup') }}
)

SELECT
    DATE_TRUNC('day', t.pickup_datetime)    AS trip_date,
    z.Borough                               AS pickup_borough,
    COUNT(*)                                AS total_trips,
    ROUND(AVG(t.fare_amount), 2)            AS avg_fare,
    ROUND(AVG(t.tip_amount), 2)             AS avg_tip,
    ROUND(SUM(t.total_amount), 2)           AS total_revenue
FROM trips t
LEFT JOIN zones z ON t.pu_location_id = z.LocationID
GROUP BY 1, 2
ORDER BY 1, 2
